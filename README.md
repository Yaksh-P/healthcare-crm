# Healthcare CRM

A local portfolio project for clinic scheduling built with Python, FastAPI, PostgreSQL, and a browser dashboard. The database starts with two fictional patients and two clinicians. Use fictional records only. The demo has no login or access controls.

## Run locally

Open Docker Desktop and wait for the engine to start. From this project folder, run:

```powershell
docker compose up --build
```

Open [Clinic dashboard](http://localhost:8000) or [interactive API documentation](http://localhost:8000/docs). The web server is bound to localhost. Stop it with Ctrl+C. PostgreSQL data persists in a named volume across restarts.

## Demo workflow

1. Add a fictional patient.
2. Select the patient and a clinician, then book a 30-minute appointment.
3. Try booking the same clinician for an overlapping time and verify that the dashboard shows a conflict. Repeat with the same patient and a different clinician.
4. Cancel the first booking and try that slot again. Mark the new booking complete.

## Database design

Appointments reference a patient and a clinician through foreign keys. Two PostgreSQL exclusion constraints prevent overlapping non-cancelled appointments for either person, even when requests arrive concurrently. Adjacent appointments can share a boundary because time ranges use an exclusive end. FastAPI returns HTTP 409 for a booking conflict, and the dashboard shows the error.

The API uses Pydantic models to validate requests. Timezone-aware timestamps are stored in PostgreSQL and displayed in the browser's local time. The PostgreSQL container runs the schema and loads sample records when it initializes a new data volume.
