import os
from dotenv import load_dotenv

# Load env before importing DB setup
load_dotenv()

from sqlalchemy import text
from app.models.db_setup import engine

def migrate():
    print(f"Running migration on dialect: {engine.dialect.name}")
    
    with engine.connect() as conn:
        try:
            # Handle PostgreSQL
            if engine.dialect.name == "postgresql":
                conn.execute(text("ALTER TABLE appointments ADD COLUMN IF NOT EXISTS google_calendar_event_id VARCHAR;"))
                conn.execute(text("ALTER TABLE appointments ADD COLUMN IF NOT EXISTS event_link VARCHAR;"))
            
            # Handle SQLite (doesn't support IF NOT EXISTS for columns in older versions)
            elif engine.dialect.name == "sqlite":
                try:
                    conn.execute(text("ALTER TABLE appointments ADD COLUMN google_calendar_event_id VARCHAR;"))
                except Exception as e:
                    if "duplicate column name" not in str(e).lower():
                        raise
                
                try:
                    conn.execute(text("ALTER TABLE appointments ADD COLUMN event_link VARCHAR;"))
                except Exception as e:
                    if "duplicate column name" not in str(e).lower():
                        raise
            
            conn.commit()
            print("Migration successful.")
            
        except Exception as e:
            conn.rollback()
            print(f"Migration failed: {e}")
            raise

if __name__ == "__main__":
    migrate()

