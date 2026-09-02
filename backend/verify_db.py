import os
from dotenv import load_dotenv

# MUST LOAD DOTENV BEFORE IMPORTING SQLAlchemy models
load_dotenv()

from sqlalchemy import text
from app.models.db_setup import engine, init_db

def verify_connection():
    db_url = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    
    print(f"Attempting to connect to: {'SQLite' if 'sqlite' in db_url else 'PostgreSQL (Supabase)'}")
    print(f"Engine dialect: {engine.dialect.name}")
    
    try:
        # Test basic connectivity
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
        print("[SUCCESS] Database connection successful.")
        
        # Initialize tables
        print("Initializing tables...")
        init_db()
        print("[SUCCESS] Tables created/verified successfully.")
        
    except Exception as e:
        print(f"[FAILED] Database connection failed: {type(e).__name__}")
        # Not printing the full error to avoid leaking credentials in logs

if __name__ == "__main__":
    verify_connection()
