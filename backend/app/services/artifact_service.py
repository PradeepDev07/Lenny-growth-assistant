import re
from typing import Any, Dict, Optional
from sqlalchemy.orm import Session

from backend.app.models.session import SessionModel
from backend.app.models.artifact import ArtifactModel
from backend.app.llm.router import model_router

ARTIFACT_SYSTEM_PROMPT = """You are an expert growth engineer and UI designer.
Your task is to generate high-quality, self-contained growth artifacts (interactive calculators, growth models, cheat sheets, or framework specifications).

CRITICAL CONSTRAINTS:
1. When generating type="html":
   - Return COMPLETE, valid HTML5 with embedded <style> and vanilla inline <script>.
   - STRICTLY FORBIDDEN: External <script src="..."> or <link rel="stylesheet" href="..."> to third-party domains.
   - Use clean, modern responsive CSS (dark/light neutral aesthetics, system fonts).
   - Make it interactive (e.g. sliders, calculation buttons, metric charts using SVG/Canvas).
2. When generating type="markdown":
   - Use structured GitHub-flavored Markdown with comparison tables, checklists, and mathematical equations.
3. Return ONLY the artifact markup/code. Do NOT wrap in conversational intro/outro.
"""


def sanitize_html_artifact(html_content: str) -> str:
    """
    Sanitize HTML code to enforce strict sandboxing:
    - Strip external script tags pointing to third-party hosts.
    - Block access to parent window, cookies, and local/session storage.
    """
    # Remove external script tags: <script src="...">
    cleaned = re.sub(
        r'<script[^>]+src=["\']?(?:https?:)?//[^>]+>.*?</script>',
        '<!-- external script removed for security -->',
        html_content,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # Neutralize dangerous APIs that could attempt cross-frame access
    forbidden_tokens = [
        "window.top",
        "window.parent",
        "document.cookie",
        "localStorage",
        "sessionStorage",
        "indexedDB",
    ]
    for token in forbidden_tokens:
        cleaned = re.sub(re.escape(token), f"/* neutralized */ null", cleaned)

    return cleaned


class ArtifactService:
    """Service generating and securing interactive artifacts."""

    def __init__(self):
        self.system_prompt = ARTIFACT_SYSTEM_PROMPT

    async def generate_artifact(
        self,
        session_id: str,
        title: str,
        artifact_type: str,
        prompt: str,
        db: Session,
        message_id: Optional[str] = None,
    ) -> ArtifactModel:
        session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")

        artifact_type = artifact_type.lower().strip()
        if artifact_type not in ("html", "markdown"):
            artifact_type = "markdown"

        user_instruction = (
            f"Title: {title}\n"
            f"Artifact Type: {artifact_type}\n"
            f"Specification:\n{prompt}\n\n"
            f"Generate the complete, production-ready artifact content now."
        )

        llm_resp, routing_meta = await model_router.generate_for_task(
            task="artifact_generation",
            messages=[{"role": "user", "content": user_instruction}],
            system=self.system_prompt,
        )

        raw_code = llm_resp.text.strip()
        # Clean markdown code blocks if the LLM wrapped it
        if raw_code.startswith("```html") and raw_code.endswith("```"):
            raw_code = raw_code[7:-3].strip()
        elif raw_code.startswith("```markdown") and raw_code.endswith("```"):
            raw_code = raw_code[11:-3].strip()
        elif raw_code.startswith("```") and raw_code.endswith("```"):
            raw_code = raw_code[3:-3].strip()

        if artifact_type == "html":
            final_content = sanitize_html_artifact(raw_code)
        else:
            final_content = raw_code

        artifact = ArtifactModel(
            session_id=session_id,
            message_id=message_id,
            title=title,
            type=artifact_type,
            content=final_content,
            model_info_json=routing_meta,
        )
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        return artifact


artifact_service = ArtifactService()
