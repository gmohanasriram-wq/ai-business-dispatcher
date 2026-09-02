# AI Business Dispatcher

AI Business Dispatcher is a system designed to automate business communications and workflows using AI voice agents, webhook integrations, and backend services.

The first demo target is a home-service business such as plumbing.

## Intended future architecture

Customer Phone Call
→ Retell AI Voice Agent
→ Webhook
→ n8n Automation
→ FastAPI Backend
→ PostgreSQL/Supabase
→ Business Rules
→ Calendar / Notifications / Lead Management

## Project Status

Phase 4: Backend Implementation

Currently Implemented:
- Retell AI Voice Agent configuration (Phase 3)
- FastAPI Backend processing (Phase 4)
- PostgreSQL/Supabase DB layer (Phase 4)
- Deterministic Business Rules (Phase 4)

Planned / Not Implemented yet:
- n8n Automation deployment
- Calendar, email, SMS, and WhatsApp integrations
- Dashboard/frontend

## Setup Instructions

1. Go to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate the Python virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\Activate.ps1
   # macOS/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the FastAPI server:
   ```bash
   uvicorn app.main:app --reload
   ```

## Verification

Health check:
http://127.0.0.1:8000/health

FastAPI docs:
http://127.0.0.1:8000/docs