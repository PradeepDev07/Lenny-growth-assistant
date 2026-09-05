import json
from typing import Any, AsyncIterator, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.app.models.session import SessionModel
from backend.app.models.message import MessageModel
from backend.app.retrieval.vector_store import vector_store
from backend.app.llm.router import model_router
from backend.app.llm.base import LLMResponse

GROUNDED_SYSTEM_PROMPT = """You are the Lenny Growth Assistant, an expert AI partner specializing in product management, growth loops, activation, retention, and startups, grounded strictly in Lenny Rachitsky's podcast interviews.

CRITICAL INSTRUCTIONS:
1. Ground your answer ONLY on the provided Transcript Context.
2. Cite the source title and guest inline whenever referencing a concept or quote (e.g. "[Elena Verna · B2B PLG]" or "[Brian Balfour · Growth Loops]").
3. If the provided context does NOT contain information to address the question, clearly state: "I could not find information on this topic in the available Lenny's Podcast transcripts." Do NOT speculate, guess, or bring in outside information.
4. Keep answers actionable, concise, and structured with clear Markdown headings and bullet points.
"""


def build_context_prompt(query: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
    """Build grounded context prompt with retrieved transcript chunks."""
    if not retrieved_chunks:
        return f"User Question: {query}\n\n[No relevant transcript chunks found in index.]"

    context_parts = ["TRANSCRIPT CONTEXT:"]
    for i, chunk in enumerate(retrieved_chunks, 1):
        context_parts.append(
            f"--- [Source {i}: {chunk['source_title']} (Guest: {chunk['guest']})] ---\n"
            f"{chunk['content']}\n"
        )

    context_parts.append(f"USER QUESTION: {query}")
    return "\n".join(context_parts)


class RAGAgent:
    """Conversational RAG agent coordinating retrieval, routing, and persistence."""

    def __init__(self):
        self.system_prompt = GROUNDED_SYSTEM_PROMPT

    def _format_history(self, db_messages: List[MessageModel], limit: int = 6) -> List[Dict[str, str]]:
        recent = db_messages[-limit:] if len(db_messages) > limit else db_messages
        formatted = []
        for m in recent:
            formatted.append({"role": m.role, "content": m.content})
        return formatted

    async def answer_query(
        self,
        session_id: str,
        user_query: str,
        db: Session,
    ) -> MessageModel:
        """Run grounded retrieval, generate response, and persist exchange."""
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # 1. Retrieve top-k transcript chunks
        chunks = vector_store.search(user_query, top_k=4, min_score=0.1)

        # 2. Persist user message
        user_msg = MessageModel(
            session_id=session_id,
            role="user",
            content=user_query,
            sources_json=[],
            model_info_json={},
        )
        db.add(user_msg)
        db.commit()

        # 3. Handle zero retrieval hits gracefully
        if not chunks:
            assistant_text = (
                "I could not find information on this topic in the available Lenny's Podcast transcripts. "
                "Try asking about B2B PLG, activation metrics (Elena Verna), growth loops vs funnels (Brian Balfour), "
                "or PM metrics and the LNO framework (Shreyas Doshi)."
            )
            model_info = {
                "task": "retrieval_qa",
                "provider": "system",
                "model": "rule_based_fallback",
                "fallback_used": False,
                "latency_ms": 0.0,
            }
            assistant_msg = MessageModel(
                session_id=session_id,
                role="assistant",
                content=assistant_text,
                sources_json=[],
                model_info_json=model_info,
            )
            db.add(assistant_msg)
            db.commit()
            db.refresh(assistant_msg)
            return assistant_msg

        # 4. Prepare prompt with history
        history = self._format_history(session.messages[:-1])
        grounded_content = build_context_prompt(user_query, chunks)
        messages_to_send = history + [{"role": "user", "content": grounded_content}]

        # 5. Invoke Model Router (task: retrieval_qa)
        llm_resp, routing_meta = await model_router.generate_for_task(
            task="retrieval_qa",
            messages=messages_to_send,
            system=self.system_prompt,
        )

        # 6. Format sources
        sources = []
        for c in chunks:
            sources.append({
                "id": c["id"],
                "source_title": c["source_title"],
                "guest": c["guest"],
                "url": c["url"],
                "chunk_index": c["chunk_index"],
                "score": c.get("score", 0.0),
                "snippet": c["content"][:240] + "...",
            })

        # 7. Persist assistant reply
        assistant_msg = MessageModel(
            session_id=session_id,
            role="assistant",
            content=llm_resp.text,
            sources_json=sources,
            model_info_json=routing_meta,
        )
        db.add(assistant_msg)
        db.commit()
        db.refresh(assistant_msg)
        return assistant_msg

    async def stream_query(
        self,
        session_id: str,
        user_query: str,
        db: Session,
    ) -> AsyncIterator[str]:
        """Stream SSE tokens with source metadata and persistence."""
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            yield f"event: error\ndata: {json.dumps({'error': 'Session not found'})}\n\n"
            return

        chunks = vector_store.search(user_query, top_k=4, min_score=0.1)

        # Persist user message
        user_msg = MessageModel(
            session_id=session_id,
            role="user",
            content=user_query,
            sources_json=[],
            model_info_json={},
        )
        db.add(user_msg)
        db.commit()

        # Format sources
        sources = []
        for c in chunks:
            sources.append({
                "id": c["id"],
                "source_title": c["source_title"],
                "guest": c["guest"],
                "url": c["url"],
                "chunk_index": c["chunk_index"],
                "score": c.get("score", 0.0),
                "snippet": c["content"][:240] + "...",
            })

        yield f"event: sources\ndata: {json.dumps(sources)}\n\n"

        if not chunks:
            disclaimer = (
                "I could not find information on this topic in the available Lenny's Podcast transcripts. "
                "Try asking about B2B PLG, activation metrics (Elena Verna), growth loops vs funnels (Brian Balfour), "
                "or PM metrics and the LNO framework (Shreyas Doshi)."
            )
            model_info = {
                "task": "retrieval_qa",
                "provider": "system",
                "model": "rule_based_fallback",
                "fallback_used": False,
            }
            yield f"event: model_info\ndata: {json.dumps(model_info)}\n\n"
            yield f"event: token\ndata: {json.dumps({'token': disclaimer})}\n\n"
            yield "event: done\ndata: {}\n\n"

            assistant_msg = MessageModel(
                session_id=session_id,
                role="assistant",
                content=disclaimer,
                sources_json=[],
                model_info_json=model_info,
            )
            db.add(assistant_msg)
            db.commit()
            return

        provider, routing_meta = await model_router.get_active_provider_for_stream("retrieval_qa")
        yield f"event: model_info\ndata: {json.dumps(routing_meta)}\n\n"

        history = self._format_history(session.messages[:-1])
        grounded_content = build_context_prompt(user_query, chunks)
        messages_to_send = history + [{"role": "user", "content": grounded_content}]

        collected_tokens = []
        try:
            async for token in provider.stream(messages_to_send, system=self.system_prompt):
                collected_tokens.append(token)
                yield f"event: token\ndata: {json.dumps({'token': token})}\n\n"
        except Exception as e:
            # Fallback text if stream fails mid-way
            err_msg = f"\n[Streaming interrupted: {str(e)}]"
            collected_tokens.append(err_msg)
            yield f"event: token\ndata: {json.dumps({'token': err_msg})}\n\n"

        full_content = "".join(collected_tokens)
        assistant_msg = MessageModel(
            session_id=session_id,
            role="assistant",
            content=full_content,
            sources_json=sources,
            model_info_json=routing_meta,
        )
        db.add(assistant_msg)
        db.commit()

        yield "event: done\ndata: {}\n\n"


rag_agent = RAGAgent()
