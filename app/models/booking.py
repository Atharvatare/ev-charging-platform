from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel, Relationship
from app.models.user import User

class Reservation(SQLModel, table=True):
    __tablename__ = "reservations"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False)
    port_id: UUID = Field(foreign_key="ports.id", nullable=False)
    start_time: datetime = Field(nullable=False)
    end_time: datetime = Field(nullable=False)
    status: str = Field(default="PENDING")         # "PENDING", "ACTIVE", "COMPLETED", "CANCELLED"
    qr_code: str = Field(nullable=False)          # Dynamic activation verification token
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    port: Optional["Port"] = Relationship(back_populates="reservations")

class WalletTransaction(SQLModel, table=True):
    __tablename__ = "wallet_transactions"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="users.id", nullable=False)
    amount: float = Field(nullable=False)           # Negative for cost, positive for deposit/credit
    transaction_type: str = Field(nullable=False)   # "DEPOSIT", "CHARGE", "REFUND"
    description: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
