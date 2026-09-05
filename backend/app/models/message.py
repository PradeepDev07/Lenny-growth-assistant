import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.db.session import Base


class MessageModel(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    sources_json = Column(JSON, nullable=True, default=list)
    model_info_json = Column(JSON, nullable=True, default=dict)

    session = relationship("SessionModel", back_populates="messages")

    @property
    def sources(self):
        return self.sources_json or []

    @sources.setter
    def sources(self, value):
        self.sources_json = value

    @property
    def model_info(self):
        return self.model_info_json or {}

    @model_info.setter
    def model_info(self, value):
        self.model_info_json = value

