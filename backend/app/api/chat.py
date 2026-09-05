from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.session import SessionModel
from backend.app.schemas.message import MessageCreate, MessageRead
from backend.app.agent.rag import rag_agent

router = APIRouter(prefix="/sessions", tags=["Chat & RAG"])


@router.post("/{session_id}/chat", response_model=MessageRead)
async def chat_with_assistant(
    session_id: str,
    message_in: MessageCreate,
    db: Session = Depends(get_db),
):
    """Send a message to the Lenny Growth Assistant and receive a grounded answer with citations."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SESSION_NOT_FOUND", "message": f"Session '{session_id}' not found."},
        )

    try:
        assistant_message = await rag_agent.answer_query(
            session_id=session_id,
            user_query=message_in.content,
            db=db,
        )
        return assistant_message
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "CHAT_GENERATION_FAILED", "message": str(e)},
        )


@router.post("/{session_id}/chat/stream")
async def chat_stream(
    session_id: str,
    message_in: MessageCreate,
    db: Session = Depends(get_db),
):
    """Stream token-by-token assistant answers via Server-Sent Events (SSE)."""
    session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SESSION_NOT_FOUND", "message": f"Session '{session_id}' not found."},
        )

    return StreamingResponse(
        rag_agent.stream_query(session_id, message_in.content, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
