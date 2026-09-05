import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from sqlalchemy import text
from backend.app.config import settings
from backend.app.db.session import init_db, SessionLocal
from backend.app.api.sessions import router as sessions_router
from backend.app.api.config import router as config_router
from backend.app.api.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize tables
    init_db()
    yield
    # Shutdown tasks


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(sessions_router)
app.include_router(config_router)
app.include_router(chat_router)




@app.get("/health")
async def health_check():
    """Health check endpoint exposing system, DB, Ollama, and Cloud LLM status."""
    db_ok = False
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception:
        db_ok = False

    ollama_ok = False


    # Check Ollama connectivity with short timeout
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            resp = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                ollama_ok = True
    except Exception:
        ollama_ok = False

    cloud_configured = bool(settings.GEMINI_API_KEY or settings.OPENROUTER_API_KEY)

    return {
        "status": "healthy",
        "db": db_ok,
        "ollama": ollama_ok,
        "cloud_llm_configured": cloud_configured,
        "version": settings.VERSION,
    }


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": str(exc)}},
    )


@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.VERSION,
        "docs": "/docs",
    }
