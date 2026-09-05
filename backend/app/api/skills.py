from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.session import SessionModel
from backend.app.skills.ship30 import ship30_skill

router = APIRouter(prefix="/sessions", tags=["Skills"])


class Ship30Request(BaseModel):
    topic: str = Field(..., min_length=2, description="Topic or prompt for the atomic essay")
    message_id: Optional[str] = Field(None, description="Optional parent message ID to transform")


@router.post("/{session_id}/skills/ship30")
async def generate_ship30_essay_endpoint(
    session_id: str,
    req: Ship30Request,
    db: Session = Depends(get_db),
):
    """Generate a high-impact Ship 30 for 30 Atomic Essay grounded in Lenny's podcast insights."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SESSION_NOT_FOUND", "message": f"Session '{session_id}' not found."},
        )

    try:
        result = await ship30_skill.generate_essay(
            session_id=session_id,
            topic=req.topic,
            db=db,
            message_id=req.message_id,
        )
        return {"status": "success", "data": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "SKILL_EXECUTION_FAILED", "message": str(e)},
        )
