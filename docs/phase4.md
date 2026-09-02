# Phase 4 Implementation Documentation

## Overview
Phase 4 introduces the FastAPI backend designed to securely receive the Retell `call_analyzed` webhook payload via n8n, apply deterministic business rules, and save information into the PostgreSQL/Supabase-compatible database.

## Architecture
The implemented architecture follows:
```
Retell AI
    ↓
n8n Production Webhook
    ↓
FastAPI Backend (POST /webhooks/retell)
    ↓
PostgreSQL / Supabase (MVP uses local SQLite via `app.db`)
    ↓
Business Rules / Actions 
```

## Database Schema
The database uses SQLAlchemy for PostgreSQL/Supabase compatibility. Using UUIDs for all primary keys.
- **businesses**: Represents the fictional NorthStar Plumbing business.
- **services**: Defines specific services/categories offered by the business (e.g., Leak Repair).
- **service_areas**: Defines areas served (e.g., Toronto, Mississauga, Brampton).
- **customers**: Tracks callers via phone_number and name.
- **leads**: Ties customer needs (service_address, service_type, problem_description, is_emergency, status) to specific service requests.
- **appointments**: Associated with a lead, capturing `preferred_date` and `preferred_time` with a `status` (requested, confirmed, cancelled).
- **call_logs**: Tracks raw payloads from Retell utilizing `call_id` as a unique idempotency key to prevent duplication.

## API Endpoints Implemented
- `GET /health` : Health check.
- `POST /webhooks/retell` : Validates incoming payload, extracts custom analysis data, executes business rules, and updates database records.
- `POST /leads` : Stub for future manual lead creation.
- `GET /availability` : Stub for querying available slots (e.g., from Google Calendar).
- `POST /appointments` : Stub for confirming appointments manually.
- `POST /notifications` : Stub for email/WhatsApp triggers.
- `POST /call-logs` : Stub for manual call logs.

## Business Rules Implemented
1. **Emergency Request**: If `is_emergency` is true or `call_outcome` is `urgent_escalation_required`, the lead is flagged as `urgent_escalation`. *No external technician dispatch is mocked or claimed.*
2. **Outside Service Area**: If `service_area_status` is `out_of_area`, the lead status is set to `out_of_area`. No appointment request is made.
3. **Normal In-Area Request**: Only if the caller is in-area, not an emergency, requested booking, and call outcome is `appointment_request` - the lead status becomes `appointment_requested` and an appointment row is created with `status="requested"`. (It is *never* marked as "confirmed" without real integration).
4. **Information Only / Incomplete**: Flaged as `incomplete` for appropriate log handling.

## Idempotency
- Implemented `call_id` based idempotency in `POST /webhooks/retell`.
- Duplicate webhook triggers are caught by checking if `call_id` exists in the `call_logs` table. If so, a `status: "duplicate"` response is immediately returned, preventing redundant leads/appointments.

## Error Handling & Security
- Validation: Leverages Pydantic in `app.schemas.retell` to enforce schema constraints.
- Payload parsing errors return `422 Unprocessable Entity` or `400 Bad Request`.
- Database failures return `500` after a rollback.
- Missing/invalid signatures throw a `401 Unauthorized` if `RETELL_WEBHOOK_SECRET` is configured in `.env`.
- Boolean normalization handles arbitrary inputs ("TRUE", "yes", etc.) gracefully without crashing.
- No access tokens or credentials are logged or exposed.

## n8n Workflow Specification
The exact workflow definition to route data from Retell through n8n into FastAPI:
1. **Webhook Node**: Production URL (`https://sri24.app.n8n.cloud/webhook/retell-call`). Listens for POST requests from Retell.
2. **Filter Event**: Ensures `event == "call_analyzed"`.
3. **HTTP Request Node**:
    - URL: `{{FASTAPI_BASE_URL}}/webhooks/retell`
    - Method: `POST`
    - Body: Send the exact raw JSON from the webhook.
4. **Switch/Router Node**: Based on FastAPI response JSON (`lead_status`), branch out to action nodes (Email notifications, external APIs - to be implemented in Phase 5).

## Testing
10 Automated `pytest` tests were added testing:
- Normal in-area appointment request
- Emergency request
- Outside-area request
- Information-only call
- Incomplete-information call
- Duplicate `call_id` protection
- Malformed payload rejection
- Boolean normalization
- Unknown service type normalization

Tests pass flawlessly and can be run with `python -m pytest tests/`.

## Left Unimplemented Intentionally
- Actual database migrations (Alembic) are skipped; the MVP relies on `create_all()`.
- Real Google Calendar / Twilio / SendGrid functionality. All external actions use clean HTTP stubs.
- Multi-tenancy routing for multiple businesses.
- Authentication/Authorization system for stubs endpoints.

