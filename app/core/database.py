import os
from sqlmodel import create_engine, SQLModel, Session

DATABASE_URL = os.getenv("DATABASE_URL")

# Auto-correct database URL prefixes for compatibility
if DATABASE_URL:
    # Support legacy postgres:// prefix (e.g. from some Supabase/Heroku connection strings)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    # Force psycopg2 driver fallback (postgresql://) which is highly stable on serverless Vercel runtimes
    if DATABASE_URL.startswith("postgresql+psycopg://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql+psycopg://", "postgresql://", 1)

if not DATABASE_URL:
    DATABASE_URL = "sqlite:///ev_charging.db"

# SQLite specific connect args: check_same_thread=False
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)

def get_session():
    """Yields a real SQLModel Session."""
    with Session(engine) as session:
        yield session

def init_db():
    """Self-healing database bootstrap."""
    # Import all models to register them with SQLAlchemy/SQLModel metadata
    from app.models.user import User
    from app.models.station import Station, Port, SolarInsight
    from app.models.booking import Reservation, WalletTransaction
    from app.models.routing import RouteTrip
    from app.models.ticket import SupportTicket

    SQLModel.metadata.create_all(engine)
    print(f"DATABASE INIT SUCCESS: Tables Synced on {DATABASE_URL.split('://')[0]} engine!")
