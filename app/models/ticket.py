import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import Field, SQLModel

class SupportTicket(SQLModel, table=True):
    __tablename__ = "support_tickets"

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    name: str = Field(nullable=False)
    email: str = Field(nullable=False)
    subject: str = Field(nullable=False)
    message: str = Field(nullable=False)
    status: str = Field(default="OPEN") # "OPEN", "RESOLVED"
    created_at: datetime = Field(default_factory=datetime.utcnow)
