from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.app.config import settings

db_url = settings.DATABASE_URL
connect_args = {}

# If PostgreSQL is configured but unreachable (e.g. running locally without Docker), fallback gracefully to SQLite
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    try:
        test_engine = create_engine(db_url, connect_args={"connect_timeout": 1} if "postgresql" in db_url else {})
        with test_engine.connect() as conn:
            pass
        test_engine.dispose()
    except Exception:
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
