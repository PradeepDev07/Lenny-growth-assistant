from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class MessageBase(BaseModel):
    role: str = Field(..., description="Role: 'user', 'assistant', or 'system'")
    content: str = Field(..., description="Message text content")
    sources: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    model_info: Optional[Dict[str, Any]] = Field(default_factory=dict)


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, description="Message text content")
    role: str = Field(default="user", description="Role: 'user', 'assistant', or 'system'")


class MessageRead(MessageBase):
    id: str
    session_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

