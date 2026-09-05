from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from backend.app.schemas.message import MessageRead
from backend.app.schemas.artifact import ArtifactRead


class SessionBase(BaseModel):
    title: Optional[str] = Field(default="New Conversation", description="Session title")
    user_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SessionCreate(SessionBase):
    pass


class SessionUpdate(BaseModel):
    title: Optional[str] = None
    user_metadata: Optional[Dict[str, Any]] = None


class SessionSummary(SessionBase):
    id: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class SessionDetail(SessionBase):
    id: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageRead] = Field(default_factory=list)
    artifacts: List[ArtifactRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

