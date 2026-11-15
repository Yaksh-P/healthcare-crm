const patientForm = document.querySelector("#patient");
const bookingForm = document.querySelector("#booking");
const schedule = document.querySelector("#schedule");
const empty = document.querySelector("#empty");
const message = document.querySelector("#message");

async function api(path, method = "GET", data) {
  const response = await fetch("/api/" + path, {
    method,
    headers: data ? { "Content-Type": "application/json" } : undefined,
    body: data ? JSON.stringify(data) : undefined,
  });
  if (response.ok) return response.json();
  const body = await response.json().catch(() => ({}));
  throw new Error(typeof body.detail === "string" ? body.detail : "The request failed. Check the form and try again.");
}

function notify(text, error = false) {
  message.textContent = text;
  message.classList.toggle("error", error);
}

function fillSelect(select, records) {
  const previous = select.value;
  select.replaceChildren(new Option("Choose…", ""), ...records.map(({ name, id }) => new Option(name, id)));
  if (records.some(({ id }) => String(id) === previous)) select.value = previous;
}

async function refreshAppointments() {
  const appointments = await api("appointments");
  const rows = appointments.map((entry) => {
    const row = document.createElement("tr");
    const starts = new Date(entry.starts_at).toLocaleString();
    for (const value of [entry.patient, entry.staff, starts, entry.status]) {
      row.insertCell().textContent = value;
    }
    const actions = row.insertCell();
    if (entry.status === "scheduled") {
      for (const [label, status] of [["Complete", "completed"], ["Cancel", "cancelled"]]) {
        const button = document.createElement("button");
        button.textContent = label;
        button.addEventListener("click", async () => {
          const buttons = [...actions.querySelectorAll("button")];
          buttons.forEach((control) => { control.disabled = true; });
          try {
            await api("appointments/" + entry.id, "PATCH", { status });
            await refreshAppointments();
            notify("Appointment " + status + ".");
          } catch (error) {
            notify(error.message, true);
          } finally {
            buttons.forEach((control) => { control.disabled = false; });
          }
        });
        actions.append(button);
      }
    }
    return row;
  });
  schedule.tBodies[0].replaceChildren(...rows);
  schedule.hidden = rows.length === 0;
  empty.hidden = rows.length > 0;
}

function handleSubmit(form, submit) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = form.querySelector("button");
    button.disabled = true;
    try {
      await submit(Object.fromEntries(new FormData(form)));
    } catch (error) {
      notify(error.message, true);
    } finally {
      button.disabled = false;
    }
  });
}

handleSubmit(patientForm, async (fields) => {
  const patient = await api("patients", "POST", fields);
  patientForm.reset();
  fillSelect(bookingForm.elements.patient_id, await api("patients"));
  bookingForm.elements.patient_id.value = patient.id;
  notify("Patient added.");
});

handleSubmit(bookingForm, async ({ duration, starts_at, ...people }) => {
  const start = new Date(starts_at);
  const end = new Date(start.getTime() + Number(duration) * 60_000);
  await api("appointments", "POST", { ...people, starts_at: start.toISOString(), ends_at: end.toISOString() });
  bookingForm.reset();
  await refreshAppointments();
  notify("Appointment booked.");
});

Promise.all([api("patients"), api("staff"), refreshAppointments()])
  .then(([patients, staff]) => {
    fillSelect(bookingForm.elements.patient_id, patients);
    fillSelect(bookingForm.elements.staff_id, staff);
  })
  .catch((error) => notify(error.message, true));
