from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text
from app.core.config import settings

# Create engine
engine = create_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)

def get_session():
    """Dependency generator for database sessions."""
    with Session(engine) as session:
        yield session

def init_db():
    """Initializes the database, loads the PostGIS extension, and builds schemas."""
    # Ensure PostGIS extension is loaded in the PostgreSQL instance
    with Session(engine) as session:
        session.exec(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        session.commit()
    
    # Create all database tables based on loaded SQLModel metadata
    # (Importing models before create_all is necessary so they register)
    from app.models.user import User
    from app.models.station import Station, Port, SolarInsight
    from app.models.booking import Reservation, WalletTransaction
    from app.models.routing import RouteTrip
    
    SQLModel.metadata.create_all(engine)
