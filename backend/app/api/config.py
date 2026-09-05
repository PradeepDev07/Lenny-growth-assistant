from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.llm.router import model_router

router = APIRouter(prefix="/config", tags=["Configuration"])


class TaskOverrideRequest(BaseModel):
    task: str = Field(..., description="Task name: retrieval_qa, essay_generation, artifact_generation, intent_routing")
    provider: str = Field(..., description="Provider name: gemini, openrouter, ollama")
    model: str = Field(..., description="Model identifier")


class ConfigResponse(BaseModel):
    routes: Dict[str, Any]
    providers: Dict[str, Any]
    recent_routing_logs: List[Dict[str, Any]]


@router.get("", response_model=ConfigResponse)
async def get_config():
    """Retrieve current routing configuration, provider reachability, and recent decisions."""
    routes = model_router.get_current_routes()
    providers = await model_router.check_provider_connectivity()
    recent_logs = model_router.routing_audit_logs[-50:]
    return ConfigResponse(
        routes=routes,
        providers=providers,
        recent_routing_logs=recent_logs,
    )


@router.post("", response_model=Dict[str, Any])
async def update_task_routing(override_in: TaskOverrideRequest):
    """Dynamically override provider/model for a specific task."""
    valid_tasks = list(model_router.DEFAULT_CHAINS.keys())
    if override_in.task not in valid_tasks:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid task '{override_in.task}'. Must be one of: {valid_tasks}",
        )

    valid_providers = ["gemini", "openrouter", "ollama"]
    if override_in.provider.lower() not in valid_providers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid provider '{override_in.provider}'. Must be one of: {valid_providers}",
        )

    model_router.set_task_override(
        task=override_in.task,
        provider=override_in.provider,
        model=override_in.model,
    )

    return {
        "status": "updated",
        "task": override_in.task,
        "effective_routes": model_router.get_current_routes(),
    }
