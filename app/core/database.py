import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

# -------------------------------------------------------------
# HIGH-SPEED IN-MEMORY STORAGE TABLES
# -------------------------------------------------------------
class MockDBStore:
    def __init__(self):
        self.users: Dict[uuid.UUID, Any] = {}
        self.stations: Dict[uuid.UUID, Any] = {}
        self.ports: Dict[uuid.UUID, Any] = {}
        self.reservations: Dict[uuid.UUID, Any] = {}
        self.solar_insights: Dict[uuid.UUID, Any] = {}
        self.wallet_transactions: List[Any] = []
        self.route_trips: List[Any] = []

# Global In-Memory Database Instance
db_store = MockDBStore()

# Mock SQLAlchemy / SQLModel Engine
engine = None

def _link_relationships(entity):
    if not entity:
        return entity
    name = entity.__class__.__name__.lower()
    if name == "station":
        entity.ports = [p for p in db_store.ports.values() if p.station_id == entity.id]
        entity.solar_insights = [s for s in db_store.solar_insights.values() if s.station_id == entity.id]
    elif name == "port":
        entity.station = db_store.stations.get(entity.station_id)
    elif name == "solarinsight":
        entity.station = db_store.stations.get(entity.station_id)
    elif name == "reservation":
        entity.port = db_store.ports.get(entity.port_id)
        if entity.port:
            entity.port.station = db_store.stations.get(entity.port.station_id)
    return entity

# -------------------------------------------------------------
# SQLALCHEMY ADAPTER CLASS (InMemorySession)
# -------------------------------------------------------------
class InMemorySession:
    def __init__(self):
        self._pending_additions = []

    def get(self, model_class, id_val):
        """Mock SQLAlchemy session.get() lookup."""
        if not id_val:
            return None
        
        # Convert string to UUID if needed
        if isinstance(id_val, str):
            try:
                id_val = uuid.UUID(id_val)
            except ValueError:
                pass
                
        name = model_class.__name__.lower()
        if name == "user":
            return db_store.users.get(id_val)
        elif name == "station":
            return _link_relationships(db_store.stations.get(id_val))
        elif name == "port":
            return _link_relationships(db_store.ports.get(id_val))
        elif name == "reservation":
            return _link_relationships(db_store.reservations.get(id_val))
        return None

    def add(self, entity):
        """Mock SQLAlchemy session.add()."""
        self._pending_additions.append(entity)

    def commit(self):
        """Mock SQLAlchemy session.commit() committing pending entities."""
        for entity in self._pending_additions:
            name = entity.__class__.__name__.lower()
            
            # Ensure entity has an ID
            if not hasattr(entity, "id") or entity.id is None:
                entity.id = uuid.uuid4()
                
            if name == "user":
                db_store.users[entity.id] = entity
            elif name == "station":
                db_store.stations[entity.id] = entity
            elif name == "port":
                db_store.ports[entity.id] = entity
            elif name == "solarinsight":
                db_store.solar_insights[entity.id] = entity
            elif name == "reservation":
                db_store.reservations[entity.id] = entity
            elif name == "wallettransaction":
                db_store.wallet_transactions.append(entity)
            elif name == "routetrip":
                db_store.route_trips.append(entity)
                
        self._pending_additions.clear()

    def refresh(self, entity):
        """Mock SQLAlchemy session.refresh() (noop in-memory)."""
        pass

    def exec(self, query):
        """Mock SQLModel session.exec() executing select statements."""
        return query.execute()

    def execute(self, statement, params=None):
        """Mock native session.execute() queries."""
        # Simple Mock return to make stations/nearby custom ST_DistanceSphere queries work!
        class MockResult:
            def fetchall(self):
                # Returns 6 SF stations as mock rows
                rows = []
                for st in db_store.stations.values():
                    rows.append((
                        st.id,
                        st.name,
                        st.address,
                        st.latitude,
                        st.longitude,
                        st.rating,
                        1200.0  # Simulated distance_meters
                    ))
                return rows
        return MockResult()

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# -------------------------------------------------------------
# FASTAPI DEPENDENCY GENERATOR
# -------------------------------------------------------------
def get_session():
    """Yields our high-speed, deadlock-free InMemorySession."""
    session = InMemorySession()
    try:
        yield session
    finally:
        session.close()

def init_db():
    """Self-healing pure-Python database bootstrap."""
    print("IN-MEMORY DB INIT: Pure Python memory schemas loaded successfully.")
