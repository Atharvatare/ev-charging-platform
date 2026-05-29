from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    email: str = Field(unique=True, index=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    full_name: Optional[str] = Field(default=None)
    role: str = Field(default="user")  # "user" or "admin"
    wallet_balance: float = Field(default=100.0)  # Seed with a default $100 starting balance
    created_at: datetime = Field(default_factory=datetime.utcnow)
