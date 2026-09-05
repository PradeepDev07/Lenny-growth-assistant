import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.orm import relationship
from backend.app.db.session import Base


class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False, default="New Conversation")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    user_metadata = Column(JSON, nullable=True, default=dict)

    messages = relationship("MessageModel", back_populates="session", cascade="all, delete-orphan", order_by="MessageModel.created_at")
    artifacts = relationship("ArtifactModel", back_populates="session", cascade="all, delete-orphan", order_by="ArtifactModel.created_at")
