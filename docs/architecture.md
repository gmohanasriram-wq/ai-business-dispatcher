# Architecture

*Planned high-level architecture for the AI Business Dispatcher system.*

## Overview

The system is designed to automate business communications via voice, webhook, and backend services.

## Components

- **Customer Phone Call**: Incoming calls handled by Retell AI Voice Agent.
- **Retell AI Voice Agent**: Processes speech, extracts intent, and triggers webhook.
- **Webhook**: HTTP endpoint receiving data from Retell.
- **n8n Automation**: Workflow automation platform orchestrating data flow.
- **FastAPI Backend**: Core API service for business logic and data processing.
- **PostgreSQL/Supabase**: Relational database for persistence.
- **Business Rules**: Engine for validating and processing data.
- **Calendar / Notifications / Lead Management**: Integrations for scheduling, alerts, and CRM.

## Data Flow

1. Customer calls the Retell-powered phone number.
2. Retell processes the call and sends structured data to a configured webhook.
3. The webhook is handled by n8n, which routes data to the FastAPI backend.
4. FastAPI processes the request, applies business rules, and interacts with the database.
5. Depending on the outcome, FastAPI may trigger calendar events, notifications, or lead updates via n8n or direct integrations.

## Notes

This document outlines the intended architecture. Implementation details will be added in later phases.