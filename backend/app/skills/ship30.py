from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from backend.app.models.session import SessionModel
from backend.app.models.message import MessageModel
from backend.app.retrieval.vector_store import vector_store
from backend.app.llm.router import model_router

SHIP30_SYSTEM_PROMPT = """You are an elite ghostwriter and growth thought leader trained in the Ship 30 for 30 atomic essay framework.

Your goal is to transform growth frameworks and podcast insights into a viral, actionable Atomic Essay (~800–1200 words).

STRICT SHIP 30/30 WRITING RUBRIC:
1. THE HOOK:
   - Start with a provocative, counter-intuitive 1-sentence hook.
   - Challenge conventional PM/growth wisdom or call out an expensive mistake.
   - Example: "90% of product teams measure activation completely wrong."

2. THE 1-3-1 RHYTHM:
   - Use the 1-3-1 cadence: 1 punchy sentence, 3 explanatory sentences, 1 takeaway sentence.
   - White space is oxygen. Keep paragraphs under 3 lines.

3. NARRATIVE ARC:
   - Act I: The Common Trap (Why most companies fail at this).
   - Act II: The Shift / Framework (The exact counter-intuitive framework from the expert).
   - Act III: The 3-Step Tactical Playbook (Concrete steps any PM or founder can run this week).
   - Act IV: The Golden Rule (One unforgettable closing principle).

4. GROUNDING & CITATIONS:
   - Weave in the exact principles and named guest quotes from the provided podcast context.
   - Credit the guest directly (e.g., "As Elena Verna proved at Miro...", "Brian Balfour's loop formula...").

5. FORMATTING:
   - Use clean Markdown with bold headers (##), bullet points, and callout quotes.
   - Include a catchy, viral title (H1) at the very top.
"""


class Ship30Skill:
    """Ship 30 for 30 essay generation engine."""

    def __init__(self):
        self.system_prompt = SHIP30_SYSTEM_PROMPT

    async def generate_essay(
        self,
        session_id: str,
        topic: str,
        db: Session,
        message_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")

        # 1. Retrieve knowledge related to the topic
        retrieved_chunks = vector_store.search(topic, top_k=4)

        context_text = ""
        if retrieved_chunks:
            context_text = "\n\n".join(
                [f"[{c['source_title']} - Guest: {c['guest']}]:\n{c['content']}" for c in retrieved_chunks]
            )

        # Also pull prior message content if a message_id was provided
        prior_context = ""
        if message_id:
            prior_msg = db.query(MessageModel).filter(MessageModel.id == message_id).first()
            if prior_msg:
                prior_context = f"\nUser Question / Context: {prior_msg.content}\n"

        prompt = (
            f"Write a high-impact Ship 30 for 30 Atomic Essay on the topic: '{topic}'.\n\n"
            f"{prior_context}\n"
            f"SOURCE MATERIAL:\n{context_text}\n\n"
            f"Follow all 5 rules of the Ship 30/30 rubric strictly."
        )

        # 2. Invoke Model Router (task: essay_generation)
        llm_resp, routing_meta = await model_router.generate_for_task(
            task="essay_generation",
            messages=[{"role": "user", "content": prompt}],
            system=self.system_prompt,
        )

        essay_text = llm_resp.text
        words = essay_text.split()
        word_count = len(words)

        # Extract title from first line if present
        lines = [line.strip() for line in essay_text.split("\n") if line.strip()]
        title = lines[0].replace("#", "").strip() if lines else f"Atomic Essay: {topic}"

        # 3. Persist essay as assistant message in the chat session
        sources = [
            {"source_title": c["source_title"], "guest": c["guest"], "url": c["url"]}
            for c in retrieved_chunks
        ]
        essay_message = MessageModel(
            session_id=session_id,
            role="assistant",
            content=essay_text,
            sources_json=sources,
            model_info_json=routing_meta,
        )
        db.add(essay_message)
        db.commit()
        db.refresh(essay_message)

        return {
            "message_id": essay_message.id,
            "title": title,
            "essay": essay_text,
            "word_count": word_count,
            "model_info": routing_meta,
            "sources": sources,
        }


ship30_skill = Ship30Skill()
