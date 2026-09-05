from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.session import SessionModel
from backend.app.models.artifact import ArtifactModel
from backend.app.schemas.artifact import ArtifactRead
from backend.app.services.artifact_service import artifact_service

router = APIRouter(tags=["Artifacts"])


class ArtifactGenerateRequest(BaseModel):
    title: str = Field(..., min_length=2, description="Title of the artifact")
    type: str = Field(default="html", description="'html' or 'markdown'")
    prompt: str = Field(..., min_length=5, description="Specification or prompt describing the artifact")
    message_id: Optional[str] = Field(None, description="Optional associated message ID")


@router.post("/sessions/{session_id}/artifacts", response_model=ArtifactRead, status_code=status.HTTP_201_CREATED)
async def create_artifact_endpoint(
    session_id: str,
    req: ArtifactGenerateRequest,
    db: Session = Depends(get_db),
):
    """Generate and persist an interactive artifact (HTML or Markdown)."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SESSION_NOT_FOUND", "message": f"Session '{session_id}' not found."},
        )

    try:
        artifact = await artifact_service.generate_artifact(
            session_id=session_id,
            title=req.title,
            artifact_type=req.type,
            prompt=req.prompt,
            db=db,
            message_id=req.message_id,
        )
        return artifact
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "ARTIFACT_GENERATION_FAILED", "message": str(e)},
        )


@router.get("/sessions/{session_id}/artifacts", response_model=List[ArtifactRead])
def list_session_artifacts(session_id: str, db: Session = Depends(get_db)):
    """List all artifacts generated in a session."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SESSION_NOT_FOUND", "message": f"Session '{session_id}' not found."},
        )
    return session.artifacts


@router.get("/artifacts/{artifact_id}", response_model=ArtifactRead)
def get_artifact(artifact_id: str, db: Session = Depends(get_db)):
    """Retrieve an artifact by ID."""
    art = db.query(ArtifactModel).filter(ArtifactModel.id == artifact_id).first()
    if not art:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ARTIFACT_NOT_FOUND", "message": f"Artifact '{artifact_id}' not found."},
        )
    return art


@router.get("/artifacts/{artifact_id}/raw")
def get_raw_artifact(artifact_id: str, db: Session = Depends(get_db)):
    """Return raw HTML or Markdown with proper Content-Type for sandboxed iframe viewing."""
    art = db.query(ArtifactModel).filter(ArtifactModel.id == artifact_id).first()
    if not art:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ARTIFACT_NOT_FOUND", "message": f"Artifact '{artifact_id}' not found."},
        )

    if art.type == "html":
        return Response(
            content=art.content,
            media_type="text/html",
            headers={
                "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline';",
                "X-Frame-Options": "SAMEORIGIN",
            },
        )
    else:
        return Response(content=art.content, media_type="text/plain")
