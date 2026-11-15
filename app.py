import os
from pathlib import Path
from typing import Annotated, Literal

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from psycopg.rows import dict_row
from pydantic import AwareDatetime, BaseModel, Field, StringConstraints, model_validator

app = FastAPI(title="Healthcare CRM", description="Local scheduling demo for fictional patients.")
static = Path(__file__).with_name("static")
app.mount("/static", StaticFiles(directory=static), name="static")


class Patient(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
    email: Annotated[str, StringConstraints(strip_whitespace=True, max_length=254)] = ""


class Booking(BaseModel):
    patient_id: Annotated[int, Field(gt=0)]
    staff_id: Annotated[int, Field(gt=0)]
    starts_at: AwareDatetime
    ends_at: AwareDatetime

    @model_validator(mode="after")
    def check_times(self):
        if self.ends_at <= self.starts_at:
            raise ValueError("End time must be after start time.")
        return self


class StatusChange(BaseModel):
    status: Literal["completed", "cancelled"]


def connect():
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(static / "index.html")


@app.get("/api/patients")
def list_patients():
    with connect() as db:
        return db.execute("SELECT * FROM patients ORDER BY name, id").fetchall()


@app.post("/api/patients", status_code=201)
def create_patient(patient: Patient):
    with connect() as db:
        return db.execute(
            "INSERT INTO patients (name, email) VALUES (%s, %s) RETURNING *",
            (patient.name, patient.email),
        ).fetchone()


@app.get("/api/staff")
def list_staff():
    with connect() as db:
        return db.execute("SELECT * FROM staff ORDER BY name, id").fetchall()


@app.get("/api/appointments")
def list_appointments():
    with connect() as db:
        return db.execute("""
            SELECT a.*, p.name AS patient, s.name AS staff
            FROM appointments a
            JOIN patients p ON p.id = a.patient_id
            JOIN staff s ON s.id = a.staff_id
            ORDER BY a.starts_at, a.id
        """).fetchall()


@app.post("/api/appointments", status_code=201)
def book(booking: Booking):
    try:
        with connect() as db:
            return db.execute("""
                INSERT INTO appointments (patient_id, staff_id, starts_at, ends_at)
                VALUES (%s, %s, %s, %s) RETURNING *
            """, (booking.patient_id, booking.staff_id, booking.starts_at, booking.ends_at)).fetchone()
    except psycopg.errors.ExclusionViolation as exc:
        raise HTTPException(409, "The patient or clinician already has an appointment in that time slot.") from exc
    except psycopg.errors.ForeignKeyViolation as exc:
        raise HTTPException(404, "Patient or clinician not found.") from exc


@app.patch("/api/appointments/{appointment_id}")
def update_status(appointment_id: int, change: StatusChange):
    with connect() as db:
        row = db.execute("SELECT * FROM appointments WHERE id = %s FOR UPDATE", (appointment_id,)).fetchone()
        if row is None:
            raise HTTPException(404, "Appointment not found.")
        if row["status"] == change.status:
            return row
        if row["status"] != "scheduled":
            raise HTTPException(409, "Only scheduled appointments can change status.")
        return db.execute(
            "UPDATE appointments SET status = %s WHERE id = %s RETURNING *",
            (change.status, appointment_id),
        ).fetchone()
