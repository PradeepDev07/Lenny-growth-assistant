from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from backend.app.db.session import get_db
from backend.app.models.session import SessionModel
from backend.app.models.message import MessageModel
from backend.app.schemas.session import SessionCreate, SessionUpdate, SessionSummary, SessionDetail
from backend.app.schemas.message import MessageCreate, MessageRead

router = APIRouter(prefix="/sessions", tags=["Sessions"])


@router.post("", response_model=SessionSummary, status_code=status.HTTP_201_CREATED)
def create_session(session_in: SessionCreate, db: Session = Depends(get_db)):
    """Create a new chat session."""
    session = SessionModel(
        title=session_in.title or "New Conversation",
        user_metadata=session_in.user_metadata or {},
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionSummary(
        id=session.id,
        title=session.title,
        user_metadata=session.user_metadata or {},
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=0,
    )


@router.get("", response_model=List[SessionSummary])
def list_sessions(db: Session = Depends(get_db)):
    """List all sessions ordered by updated_at desc, with message counts."""
    sessions = (
        db.query(
            SessionModel,
            func.count(MessageModel.id).label("message_count"),
        )
        .outerjoin(MessageModel, SessionModel.id == MessageModel.session_id)
        .group_by(SessionModel.id)
        .order_by(desc(SessionModel.updated_at))
        .all()
    )

    result = []
    for s, count in sessions:
        result.append(
            SessionSummary(
                id=s.id,
                title=s.title,
                user_metadata=s.user_metadata or {},
                created_at=s.created_at,
                updated_at=s.updated_at,
                message_count=count,
            )
        )
    return result


@router.get("/{session_id}", response_model=SessionDetail)
def get_session(session_id: str, db: Session = Depends(get_db)):
    """Get session details with full message history and artifacts."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SESSION_NOT_FOUND", "message": f"Session '{session_id}' was not found."},
        )
    return session


@router.patch("/{session_id}", response_model=SessionSummary)
def update_session(session_id: str, update_in: SessionUpdate, db: Session = Depends(get_db)):
    """Update session title or metadata."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SESSION_NOT_FOUND", "message": f"Session '{session_id}' was not found."},
        )

    if update_in.title is not None:
        session.title = update_in.title
    if update_in.user_metadata is not None:
        session.user_metadata = update_in.user_metadata

    db.commit()
    db.refresh(session)
    count = db.query(MessageModel).filter(MessageModel.session_id == session.id).count()
    return SessionSummary(
        id=session.id,
        title=session.title,
        user_metadata=session.user_metadata or {},
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=count,
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: str, db: Session = Depends(get_db)):
    """Delete a session and all its messages/artifacts."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SESSION_NOT_FOUND", "message": f"Session '{session_id}' was not found."},
        )
    db.delete(session)
    db.commit()
    return None


@router.get("/{session_id}/messages", response_model=List[MessageRead])
def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    """Fetch messages for a specific session."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SESSION_NOT_FOUND", "message": f"Session '{session_id}' was not found."},
        )
    return session.messages


@router.post("/{session_id}/messages", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
def post_session_message(session_id: str, message_in: MessageCreate, db: Session = Depends(get_db)):
    """Persist a message into session history."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SESSION_NOT_FOUND", "message": f"Session '{session_id}' was not found."},
        )

    msg = MessageModel(
        session_id=session_id,
        role=message_in.role,
        content=message_in.content,
        sources_json=[],
        model_info_json={},
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg
