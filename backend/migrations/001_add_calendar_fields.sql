-- Safe, idempotent migration to add calendar fields to appointments table
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS google_calendar_event_id VARCHAR;
ALTER TABLE appointments ADD COLUMN IF NOT EXISTS event_link VARCHAR;

