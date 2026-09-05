import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.config import settings

logger = logging.getLogger("database")

db_url = settings.DATABASE_URL
connect_args = {}

# Handle legacy postgres:// URLs from cloud providers (Render, Supabase, Railway)
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# In development, if PostgreSQL is configured but unreachable, fallback gracefully to SQLite
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif settings.ENVIRONMENT == "development":
    try:
        test_engine = create_engine(db_url, connect_args={"connect_timeout": 5} if "postgresql" in db_url else {})
        with test_engine.connect() as conn:
            pass
        test_engine.dispose()
    except Exception as err:
        logger.warning(
            "PostgreSQL is unreachable in development (%s). Falling back gracefully to SQLite: growth_assistant.db",
            err,
        )
        db_url = "sqlite:///./growth_assistant.db"
        connect_args = {"check_same_thread": False}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    echo=False,
    pool_pre_ping=True if not db_url.startswith("sqlite") else False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency for obtaining database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
