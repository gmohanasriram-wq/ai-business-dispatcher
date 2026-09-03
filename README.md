# AI Business Dispatcher

An AI-powered voice dispatcher and workflow automation system for home-service businesses. The system converts customer phone conversations into structured business events, routes them through n8n and FastAPI, applies deterministic business rules, checks Google Calendar availability, creates appointments, and persists booking state in PostgreSQL/Supabase.

The system is configured around **NorthStar Plumbing**, a fictional home-service business used as a realistic demonstration environment.

---

## Demo

- **Video Walkthrough:** `[Demo Video Placeholder]`
- **Interactive Call Recording & Transcript:** `[Call Sample Placeholder]`
- **Live Architecture & Execution Trace:** `[Screenshots Placeholder]`

---

## Problem

Home-service businesses (plumbing, HVAC, electrical) face persistent operational friction in dispatching and lead capture:

- **Missed Revenue from Unanswered Calls:** Up to 30% of incoming customer calls go to voicemail during peak hours or after business hours, leading callers to immediately contact competitors.
- **Manual, High-Latency Intake:** Dispatchers manually transcribe caller details, assess urgency, check technician calendars, and enter records into fragmented systems.
- **Mishandled Emergencies:** Critical issues such as burst pipes or active flooding are often queued behind routine inquiries rather than instantly escalated.
- **Scheduling Conflicts & Double-Booking:** Fragmented booking calendars and lack of immediate availability checks lead to customer frustration and scheduling overlaps.
- **Inconsistent Data & Human Error:** Unstructured call notes lead to missing callback numbers, incorrect service addresses, and incomplete job descriptions.

---

## Solution

The AI Business Dispatcher automates the entire front-office intake and scheduling lifecycle:

1. **24/7 Voice Intake:** A conversational AI agent greets callers, collects structured customer and problem information, identifies service areas, and detects emergencies.
2. **Deterministic Routing:** Business rules are executed in code rather than left to probabilistic LLM decisions, guaranteeing consistent handling for emergencies, out-of-area requests, and bookings.
3. **Automated Scheduling:** Verified appointment requests trigger real-time Google Calendar availability checks and event creation without dispatcher intervention.
4. **State Persistence & Auditability:** All raw calls, customer identities, leads, and confirmed calendar appointments are persisted in a relational PostgreSQL schema.
5. **Multi-Layer Reliability:** Idempotency keys, concurrent replay guards, transaction rollbacks, and sanitized error responses ensure resilience against network retries and duplicate webhooks.

---

## Architecture

The project follows a strict separation of concerns across four core phases:
- **Phase 4 (Decides & Routes):** FastAPI evaluates deterministic business rules and normalizes payloads.
- **Phase 5 (Stores & Serves):** PostgreSQL/Supabase provides persistent relational storage.
- **Phase 6 (Acts Externally):** n8n Cloud coordinates availability checks and Google Calendar event creation.
- **Phase 7 (Hardens Reliability):** End-to-end idempotency, concurrency protection, and transaction safety.

```mermaid
flowchart TD
    A[Customer Phone Call] -->|Voice Stream| B[Retell AI Voice Agent]
    B -->|call_analyzed Webhook| C[n8n Cloud Workflow]
    C -->|POST /webhooks/retell| D[FastAPI Backend]
    
    subgraph FastAPI_Backend [FastAPI & Business Logic Engine]
        D --> E{Idempotency Check}
        E -->|Existing call_id| E1[Return Duplicate Status]
        E -->|New call_id| F[Save CallLog & Customer]
        F --> G{Deterministic Business Rules}
        G -->|is_emergency or urgent_escalation| H[Lead: urgent_escalation]
        G -->|service_area_status: out_of_area| I[Lead: out_of_area]
        G -->|info_only or incomplete| J[Lead: incomplete]
        G -->|in_area & booking_requested| K[Lead: appointment_requested<br/>Create Requested Appointment]
        H & I & J & K --> L[(PostgreSQL / Supabase)]
    end

    D -->|HTTP 200 with lead_status| C

    subgraph n8n_Orchestration [n8n Automation Engine]
        C --> M{Routing Switch}
        M -->|urgent_escalation| N[Trigger Urgent Alert Stub]
        M -->|out_of_area / incomplete| O[Log Non-Booking Outcome]
        M -->|appointment_requested| P[Eligibility Guard]
        P --> Q[Check Google Calendar Availability]
        Q -->|Slot Available| R[Create Google Calendar Event]
        R --> S[POST /appointments]
    end

    subgraph Appointment_Persistence [Appointment Confirmation]
        S --> T[FastAPI POST /appointments]
        T --> U{Verify Existing Appointment}
        U -->|Already Confirmed Same Event ID| V[Return already_confirmed 200]
        U -->|Confirmed Different Event ID| W[Return Conflict 409]
        U -->|Valid New Confirmation| X[Update Status: confirmed<br/>Save google_calendar_event_id<br/>Commit to Supabase]
        X --> L
    end
```

---

## Key Features

- **Conversational Voice Intake:** Powered by Retell AI with sub-second response latency and natural turn-taking.
- **Structured Post-Call Extraction:** Extracts strongly typed fields (customer name, callback number, address, city, service type, emergency flag, preferred time, booking request).
- **Deterministic Business Rules:** Eliminates LLM hallucinations for operational decisions; code enforces emergency classification and boundary checks.
- **Strict Service Area Boundaries:** Fictional service territory strictly limited to Toronto, Mississauga, and Brampton.
- **Appointment Eligibility Guard:** Validates address, in-area status, non-emergency classification, and customer intent before allowing any calendar interaction.
- **Real-Time Calendar Scheduling:** Checks slot availability and creates events directly in Google Calendar in the `America/Toronto` timezone.
- **Two-Phase Booking Lifecycle:** Appointments transition from `requested` (voice call intake) to `confirmed` (after calendar creation and backend verification).
- **Multi-Level Idempotency:** Prevents duplicate leads or calendar bookings across retried webhooks or replayed network requests.
- **Data Hardening & Sanitization:** Normalizes empty/whitespace phone numbers to `None` to prevent unique constraint collisions; sanitizes internal database errors to prevent metadata leaks.
- **Zero-PII Structured Logging:** Lightweight logging traces `call_id`, `lead_id`, and `event_id` through the pipeline without logging sensitive caller data.
- **Automated Test Suite:** 21 automated pytest tests verifying business rules, edge cases, error sanitization, and confirmation idempotency.

---

## End-to-End Flow

```
1. Customer Call
   └── Customer dials NorthStar Plumbing; Retell AI answers and conducts intake.
2. Structured Extraction
   └── Retell extracts caller intent, problem summary, address, and preferred time.
3. Webhook Delivery
   └── Retell dispatches call_analyzed payload to the n8n webhook endpoint.
4. FastAPI Ingestion & Rules Evaluation
   └── n8n relays the payload to FastAPI (POST /webhooks/retell).
   └── FastAPI checks call_id idempotency in call_logs.
   └── Customer and Lead records are created in PostgreSQL/Supabase.
   └── Business rules assign lead_status = "appointment_requested" and insert an Appointment record with status = "requested".
5. n8n Routing & Eligibility Guard
   └── n8n inspects lead_status.
   └── Eligibility Guard verifies booking_requested=true, is_emergency=false, and service_area_status="in_area".
6. Calendar Integration
   └── n8n queries Google Calendar for conflicting events in the requested window.
   └── A calendar event is created with the customer's name, problem description, and address.
7. Backend Persistence
   └── n8n posts the confirmation payload to FastAPI (POST /appointments) containing lead_id, call_id, and google_calendar_event_id.
   └── FastAPI updates the appointment record to status = "confirmed" and persists the Google Calendar ID and event link.
8. Idempotent Safety
   └── Any replayed or duplicate webhook returns cached/confirmed responses without duplicate bookings or database collisions.
```

> **Design Note:** The voice agent intentionally does **not** claim an appointment is confirmed during the call. It informs the caller that their preferred window has been recorded for dispatch verification. Confirmation occurs downstream after availability validation.

---

## AI Voice Agent

The voice agent is built using Retell AI and configured specifically for NorthStar Plumbing dispatching.

### Core Agent Guidelines
- **Identity:** Calm, professional dispatcher for a local home-service business.
- **Inquiry Pace:** Asks one clear question at a time; does not overwhelm the caller.
- **Scope Discipline:** Never diagnoses plumbing faults or provides DIY repair instructions.
- **Emergency Protocol:** Immediately prioritizes safety and flags active flooding/burst pipes as urgent; advises callers in physical danger to contact emergency services.
- **Honesty Guardrail:** Never says "Your appointment is booked" or "A technician is dispatched." Always uses: *"I have noted your preferred time for the dispatch team."*

### Post-Call Extraction Contract
Upon call completion, Retell extracts this typed schema:

| Field | Type | Description |
| :--- | :--- | :--- |
| `customer_name` | String / Null | Full name stated by caller |
| `phone_number` | String / Null | Caller callback number |
| `service_address` | String / Null | Specific street address |
| `city` | String / Null | Service city |
| `service_type` | String / Null | Category (`leak`, `drain_clog`, `burst_pipe`, `water_heater`, etc.) |
| `problem_description` | String / Null | Concise factual summary of the issue |
| `is_emergency` | Boolean | `true` only for active flooding, burst pipes, or immediate property risk |
| `preferred_date` | String / Null | Requested service date |
| `preferred_time` | String / Null | Requested service time window |
| `booking_requested` | Boolean | `true` if customer requested service scheduling |
| `service_area_status` | Selector | `in_area` (Toronto, Mississauga, Brampton), `out_of_area`, or `unknown` |
| `call_outcome` | Selector | `appointment_request`, `urgent_escalation_required`, `out_of_area_follow_up`, `information_only`, `incomplete_information` |

---

## Automation Layer (n8n Cloud)

The orchestration workflow is hosted on n8n Cloud:

1. **Webhook Trigger:** Receives incoming Retell `call_analyzed` JSON payloads.
2. **FastAPI Relay Node:** Sends the raw payload to Render FastAPI (`POST /webhooks/retell`).
3. **Switch Router:** Evaluates the returned `lead_status`:
   - `urgent_escalation`: Routes to emergency notification channels.
   - `out_of_area`: Flags record for boundary follow-up.
   - `incomplete`: Archives record for dispatcher review.
   - `appointment_requested`: Enters scheduling pipeline.
4. **Appointment Scheduling Pipeline:**
   - **Eligibility Guard:** Confirms `booking_requested == true` and `is_emergency == false`.
   - **Availability Check:** Queries Google Calendar events for the requested date and time.
   - **Event Creation:** Creates a calendar event with service address and issue summary in `America/Toronto` timezone.
   - **Prepare Backend Persistence:** Formats `lead_id`, `call_id`, `google_calendar_event_id`, and `event_link`.
   - **Backend Persistence HTTP Request:** Sends `POST /appointments` to FastAPI to confirm booking state in the database.

---

## Backend (FastAPI)

The backend service is built with FastAPI and SQLAlchemy, using Python 3.11+.

### Implemented Endpoints

| Method | Endpoint | Purpose | Request Body | Response |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | Service health & liveness check | None | `{"status": "ok", "service": "ai-business-dispatcher"}` |
| `POST` | `/webhooks/retell` | Ingests Retell payload, runs rules, stores lead | `RetellWebhookPayload` | `{"status": "success", "call_id": "...", "lead_id": "...", "lead_status": "..."}` |
| `POST` | `/appointments` | Confirms booking with Google Calendar ID | `AppointmentConfirmationRequest` | `{"status": "success", "appointment_id": "...", "google_calendar_event_id": "..."}` |
| `POST` | `/leads` | Extensibility stub for manual lead intake | `Dict[str, Any]` | `{"status": "success", "message": "Lead stub created"}` |
| `GET` | `/availability` | Extensibility stub for direct calendar reads | None | `{"status": "success", "availability": []}` |
| `POST` | `/notifications`| Extensibility stub for messaging triggers | `Dict[str, Any]` | `{"status": "success", "message": "Notification stub triggered"}` |
| `POST` | `/call-logs` | Extensibility stub for manual call logging | `Dict[str, Any]` | `{"status": "success", "message": "Call log stub created"}` |

---

## Data Layer (PostgreSQL / Supabase)

Database persistence uses SQLAlchemy 2.0 with the synchronous `psycopg` (v3) driver connecting directly to PostgreSQL on Supabase (with automatic SQLite fallback for local development).

```mermaid
erDiagram
    businesses ||--o{ service_areas : "operates in"
    businesses ||--o{ services : "offers"
    customers ||--o{ leads : "submits"
    leads ||--o{ appointments : "requests"
    call_logs {
        string id PK
        string call_id UK "Idempotency Key"
        string agent_id
        string agent_name
        string status
        json raw_payload
        datetime created_at
    }
    customers {
        string id PK
        string name
        string phone_number UK
        datetime created_at
        datetime updated_at
    }
    leads {
        string id PK
        string customer_id FK
        string service_address
        string city
        string service_type
        text problem_description
        boolean is_emergency
        string status
        datetime created_at
        datetime updated_at
    }
    appointments {
        string id PK
        string lead_id FK
        string preferred_date
        string preferred_time
        string status
        string google_calendar_event_id
        string event_link
        datetime created_at
        datetime updated_at
    }
    businesses {
        string id PK
        string name
        datetime created_at
        datetime updated_at
    }
    service_areas {
        string id PK
        string business_id FK
        string city
        boolean is_active
        datetime created_at
    }
    services {
        string id PK
        string business_id FK
        string name
        string category
        text description
        boolean is_active
        datetime created_at
        datetime updated_at
    }
```

### Table Responsibilities
- **`call_logs`**: Stores raw webhook payloads from Retell with a `UNIQUE` constraint on `call_id` to enforce webhook-level idempotency.
- **`customers`**: Deduplicates customer profiles via unique `phone_number`.
- **`leads`**: Central record tracking address, problem description, emergency classification, and business rule routing status (`urgent_escalation`, `out_of_area`, `incomplete`, `appointment_requested`, `new`).
- **`appointments`**: Manages scheduling state (`requested` -> `confirmed`), storing `google_calendar_event_id` and web event links.
- **`businesses`, `service_areas`, `services`**: Reference tables defining company boundaries and catalog offerings.

---

## Reliability Engineering

Phase 7 introduced explicit hardening mechanisms to protect against distributed failures:

1. **Idempotent Appointment Confirmation:**
   If n8n retries `POST /appointments` with the same `google_calendar_event_id`, the endpoint returns HTTP 200 with `status: "already_confirmed"` without re-writing or corrupting data. If an attempt is made to overwrite an existing appointment with a *different* calendar event ID, it rejects the request with `HTTP 409 Conflict`.
2. **Concurrent Replay & Webhook Idempotency:**
   Incoming calls check `CallLog.call_id`. If two identical requests race past the query check simultaneously, the PostgreSQL unique index raises an `IntegrityError`, which is caught, rolled back, and gracefully resolved to a clean `{"status": "duplicate"}` HTTP 200 response instead of an unhandled 500.
3. **Transactional Integrity & Rollback:**
   All mutating database operations in `/webhooks/retell` and `/appointments` are guarded with explicit `try...except` blocks that execute `db.rollback()` on failure before returning clean, sanitized HTTP 500 errors.
4. **Sanitized Error Responses:**
   Database exception strings (`str(e)`) are logged internally on the server with stack traces but are never exposed in public API responses, preventing database schema or credential leakage.
5. **Empty Phone Number Normalization:**
   In PostgreSQL, `NULL` values do not violate unique indexes, but empty strings `""` do. Pydantic validators normalize empty and whitespace-only phone strings to `None` prior to database operations, preventing unique constraint crashes when successive callers do not provide a phone number.
6. **Zero-PII Structured Logging:**
   Application loggers (`dispatcher.webhooks`, `dispatcher.retell_handler`, `dispatcher.appointments`) output structured logs tracing `call_id`, `lead_id`, and `event_id` without outputting customer names, phone numbers, or addresses.

---

## Testing

The test suite consists of **21 automated pytest tests** executed against an isolated SQLite test database with zero external dependencies.

```bash
cd backend
pytest
```

### Test Coverage Breakdown

```
tests/test_appointments.py (7 tests)
├── test_confirm_appointment_success                    # Verifies status transition to confirmed & event_id persistence
├── test_confirm_appointment_idempotency                # Verifies identical repeat confirmation returns already_confirmed
├── test_confirm_appointment_conflict                   # Verifies different event ID on confirmed appointment returns 409
├── test_confirm_appointment_not_found                  # Verifies non-existent lead_id returns 404
├── test_confirm_appointment_missing_event_id           # Verifies missing event ID triggers 422 validation error
├── test_confirm_appointment_unconfirmed_rejected       # Verifies booking_confirmed=false is rejected with 422
└── test_confirm_appointment_commit_failure_sanitized   # Verifies commit failure triggers rollback & sanitized 500

tests/test_business_rules.py (14 tests)
├── test_health                                         # Verifies GET /health liveness check
├── test_normal_in_area_appointment_request             # Verifies in-area appointment path creates lead & requested appt
├── test_emergency_request                              # Verifies burst pipe/emergency leads route to urgent_escalation
├── test_outside_area_request                           # Verifies non-service city leads route to out_of_area
├── test_information_only_call                          # Verifies general inquiry routes to incomplete
├── test_incomplete_information_call                    # Verifies missing caller details route to incomplete
├── test_duplicate_call_id                              # Verifies sequential replay of same call_id returns duplicate
├── test_malformed_payload                              # Verifies invalid schema returns 422
├── test_boolean_normalization                          # Verifies string booleans ("TRUE", "false") normalize correctly
├── test_unknown_service_type                           # Verifies unrecognized service requests are preserved safely
├── test_service_model_creation                         # Verifies Service catalog model relationship
├── test_empty_string_phone_number_successive_calls     # Verifies consecutive callers with "" phone don't crash unique index
├── test_webhook_database_error_sanitized               # Verifies DB exceptions return generic 500 without leaking details
└── test_concurrent_duplicate_webhook_integrity_error   # Verifies race condition IntegrityError recovers to duplicate 200
```

---

## Deployment

The production deployment architecture connects five coordinated platforms:

- **FastAPI Backend:** Deployed on **Render** as a Python web service configured via `render.yaml`.
- **Database:** Managed **Supabase PostgreSQL** instance connecting over SSL with SQLAlchemy connection pooling.
- **Workflow Automation:** **n8n Cloud** orchestrating webhook relays, calendar queries, and conditional logic.
- **Voice Agent:** **Retell AI** handling telephony and real-time audio conversation.
- **Calendar:** **Google Calendar API** executing availability checks and booking reservations in `America/Toronto`.

---

## Project Structure

```
ai-business-dispatcher/
├── .gitignore
├── LICENSE
├── README.md
├── render.yaml                          # Render Blueprint deployment configuration
├── backend/
│   ├── .env.example                     # Environment variables template
│   ├── requirements.txt                 # Runtime & test dependencies
│   ├── run_migration.py                 # Multi-dialect database column migration script
│   ├── verify_db.py                     # Safe database connectivity & table check script
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                      # FastAPI application entry point & router inclusion
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── database.py              # SQLAlchemy ORM models (7 tables)
│   │   │   └── db_setup.py              # Engine setup, sessionmaker & driver normalization
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── appointments.py          # Real POST /appointments confirmation endpoint
│   │   │   ├── stubs.py                 # Extensibility stubs for future integrations
│   │   │   └── webhooks.py              # POST /webhooks/retell webhook receiver
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── appointment.py           # AppointmentConfirmationRequest Pydantic schema
│   │   │   └── retell.py                # RetellWebhookPayload & CustomAnalysisData schemas
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── retell_handler.py        # Business rules evaluation & database transaction service
│   │   └── utils/
│   │       └── __init__.py
│   ├── migrations/
│   │   └── 001_add_calendar_fields.sql  # Safe SQL migration for calendar fields
│   └── tests/
│       ├── test_appointments.py         # 7 appointment persistence & idempotency tests
│       └── test_business_rules.py       # 14 webhook routing & reliability tests
├── docs/
│   ├── architecture.md                  # High-level component specifications
│   ├── demo-scenarios.md                # Demonstration call scenarios
│   ├── phase4.md                        # Phase 4 implementation documentation
│   └── voice-agent.md                   # Retell agent prompt & extraction documentation
└── workflows/
    └── README.md                        # n8n workflow documentation notes
```

---

## Local Development

### Prerequisites
- Python 3.11+
- Git

### Setup Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/gmohanasriram-wq/ai-business-dispatcher.git
   cd ai-business-dispatcher
   ```

2. **Set up virtual environment:**
   ```bash
   cd backend
   python -m venv venv
   
   # Windows:
   .\venv\Scripts\Activate.ps1
   
   # macOS / Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   *(By default, leaving `DATABASE_URL` unset will safely fallback to local SQLite `sqlite:///./app.db`)*

5. **Verify database connection & run migrations:**
   ```bash
   python verify_db.py
   python run_migration.py
   ```

6. **Run automated test suite:**
   ```bash
   pytest
   ```

7. **Start local development server:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

8. **Verify endpoints:**
   - Health check: `http://127.0.0.1:8000/health`
   - Interactive OpenAPI docs: `http://127.0.0.1:8000/docs`

---

## Environment Variables

Configure these variables in `backend/.env` for local execution or within the Render dashboard for production:

| Variable | Required | Description | Example / Default |
| :--- | :--- | :--- | :--- |
| `APP_ENV` | No | Application environment mode | `development` / `production` |
| `DATABASE_URL` | No | PostgreSQL connection string (defaults to SQLite if unset) | `postgresql+psycopg://user:pass@host:5432/postgres` |
| `RETELL_WEBHOOK_SECRET` | No | HMAC-SHA256 signature secret for Retell requests | `your_webhook_secret` |
| `RETELL_API_KEY` | No | Retell API key for programmatic agent queries | `your_retell_api_key` |
| `FASTAPI_BASE_URL` | No | Base URL of deployed FastAPI application | `https://ai-business-dispatcher.onrender.com` |
| `N8N_WEBHOOK_URL` | No | URL of n8n production webhook receiver | `https://sri24.app.n8n.cloud/webhook/...` |
| `NOTIFICATION_EMAIL` | No | Email destination for urgent alerts | `dispatch@northstarplumbing.demo` |
| `PYTHON_VERSION` | No | Python runtime version for Render deployment | `3.11.9` |

---

## Example API Flow

### 1. Inbound Webhook (`POST /webhooks/retell`)

**Request Body:**
```json
{
  "event": "call_analyzed",
  "call": {
    "call_id": "call_sample_98765",
    "agent_id": "agent_northstar_01",
    "agent_name": "NorthStar Dispatcher",
    "call_status": "completed",
    "call_analysis": {
      "custom_analysis_data": {
        "customer_name": "Sarah Connor",
        "phone_number": "+14165550199",
        "service_address": "456 Bay Street",
        "city": "Toronto",
        "service_type": "leaking kitchen pipe",
        "problem_description": "Under-sink pipe dripping steadily into cabinet.",
        "is_emergency": false,
        "preferred_date": "2026-09-05",
        "preferred_time": "10:00 AM",
        "booking_requested": true,
        "service_area_status": "in_area",
        "call_outcome": "appointment_request"
      }
    }
  }
}
```

**Response (`200 OK`):**
```json
{
  "status": "success",
  "call_id": "call_sample_98765",
  "lead_id": "d3b07384-d113-46c1-a83a-d46779a5286a",
  "lead_status": "appointment_requested",
  "action": "completed"
}
```

### 2. Appointment Persistence (`POST /appointments`)

**Request Body:**
```json
{
  "call_id": "call_sample_98765",
  "lead_id": "d3b07384-d113-46c1-a83a-d46779a5286a",
  "google_calendar_event_id": "gcal_event_abc123xyz",
  "event_link": "https://calendar.google.com/calendar/event?eid=YWJjMTIzeHl6",
  "booking_confirmed": true
}
```

**Response (`200 OK`):**
```json
{
  "status": "success",
  "appointment_id": "e8a937b2-6019-482f-871d-7203b573619a",
  "google_calendar_event_id": "gcal_event_abc123xyz",
  "message": "Appointment confirmed and persisted"
}
```

---

## Design Decisions

1. **Deterministic Business Rules vs. LLM Autonomy:**
   While LLMs excel at speech understanding and natural entity extraction, they should not be granted direct authority to book appointments, dispatch emergency services, or determine service area eligibility. Business rules in code provide testable, auditable, and deterministic control.
2. **Downstream Confirmation vs. In-Call Promises:**
   The voice agent explicitly records customer preferences without guaranteeing availability or confirming slots during the phone conversation. Actual booking occurs after calendar conflict checks succeed, eliminating caller confusion or double-bookings.
3. **Multi-Tiered Idempotency:**
   Telephony and automation webhooks are subject to at-least-once delivery semantics. Both `/webhooks/retell` (via `call_logs.call_id`) and `/appointments` (via state checking and calendar event matching) enforce strict idempotency so duplicate deliveries do not duplicate records or appointments.
4. **Relational Data Integrity:**
   Storing booking state, leads, and raw payloads in PostgreSQL provides an audit trail that decoupled webhook platforms cannot guarantee on their own.
5. **Pre-Action Eligibility Guard:**
   Before invoking third-party Google Calendar APIs, an explicit guard verifies boundary, non-emergency, and customer intent criteria, conserving external API quota and avoiding calendar clutter.
6. **Timezone Uniformity:**
   All calendar operations and time windows explicitly run in `America/Toronto` to avoid local host server timezone drift.

---

## Limitations / Future Improvements

- **Outbound Notification Channels:** Integration of real Twilio SMS or SendGrid email notifications for instant customer confirmation messages (currently stubbed at `/notifications`).
- **Two-Way Calendar Sync:** Webhook listeners for technician calendar cancellations or manual event moves inside Google Calendar to update Supabase appointment status.
- **Technician Routing & Skill Matching:** Dispatch algorithms assigning specific jobs based on technician licensing, vehicle inventory, or GPS location.
- **Administrative Web Dashboard:** Front-end operations portal (e.g. Next.js) for viewing live dispatch queues, listening to call recordings, and overriding lead statuses.
- **CRM Integrations:** Direct sync with field-service management platforms (e.g. Jobber, ServiceTitan).

---

## Portfolio Context

> **Disclaimer:** This repository is a portfolio and demonstration project using a fictional home-service business (**NorthStar Plumbing**) to demonstrate AI voice automation, backend system integration, workflow orchestration, database persistence, and reliability engineering.

---

## License

This project is licensed under the [MIT License](LICENSE).