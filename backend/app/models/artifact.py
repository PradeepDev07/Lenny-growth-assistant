import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.db.session import Base


class ArtifactModel(Base):
    __tablename__ = "artifacts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    message_id = Column(String(36), nullable=True)
    title = Column(String(255), nullable=False)
    type = Column(String(20), nullable=False)  # 'markdown', 'html'
    content = Column(Text, nullable=False)
    model_info_json = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    session = relationship("SessionModel", back_populates="artifacts")

    @property
    def model_info(self):
        return self.model_info_json or {}

    @model_info.setter
    def model_info(self, value):
        self.model_info_json = value

