from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ArtifactBase(BaseModel):
    title: str = Field(..., description="Artifact title")
    type: str = Field(..., description="'markdown' or 'html'")
    content: str = Field(..., description="Artifact code or markup content")
    model_info: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ArtifactCreate(ArtifactBase):
    message_id: Optional[str] = None


class ArtifactRead(ArtifactBase):
    id: str
    session_id: str
    message_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

