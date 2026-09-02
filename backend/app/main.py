from fastapi import FastAPI
from .routes import webhooks, stubs, appointments
from .models.db_setup import init_db

# Initialize database
init_db()

app = FastAPI(
    title="AI Business Dispatcher",
    version="0.1.0"
)

app.include_router(webhooks.router)
app.include_router(stubs.router)
app.include_router(appointments.router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "ai-business-dispatcher"}