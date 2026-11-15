CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TABLE patients (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL,
    email text NOT NULL DEFAULT ''
);

CREATE TABLE staff (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL
);

CREATE TABLE appointments (
    id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    patient_id integer NOT NULL REFERENCES patients(id),
    staff_id integer NOT NULL REFERENCES staff(id),
    starts_at timestamptz NOT NULL,
    ends_at timestamptz NOT NULL,
    status text NOT NULL DEFAULT 'scheduled'
        CHECK (status IN ('scheduled', 'completed', 'cancelled')),
    CHECK (starts_at < ends_at),
    EXCLUDE USING gist (
        staff_id WITH =,
        tstzrange(starts_at, ends_at, '[)') WITH &&
    ) WHERE (status <> 'cancelled'),
    EXCLUDE USING gist (
        patient_id WITH =,
        tstzrange(starts_at, ends_at, '[)') WITH &&
    ) WHERE (status <> 'cancelled')
);

INSERT INTO staff (name) VALUES ('Dr. Avery Chen'), ('Dr. Maya Brooks');
INSERT INTO patients (name, email)
VALUES ('Jordan Lee', 'jordan@example.test'), ('Taylor Morgan', 'taylor@example.test');
