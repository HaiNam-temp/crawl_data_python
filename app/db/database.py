from typing import Optional
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Load database url from environment. In containers ensure you pass this at runtime
DATABASE_URL: Optional[str] ="postgresql://cosign:Cosign2025@167.71.200.141:5432/cosign_db"
if not DATABASE_URL:
    # Allow a developer-friendly fallback to sqlite when running locally or in test containers.
    # Enable explicitly with FALLBACK_TO_SQLITE=1 or when ENV is not 'production'.
    fallback_flag = os.getenv("FALLBACK_TO_SQLITE", "").lower()
    env_name = os.getenv("ENV", "development").lower()
    if fallback_flag in ("1", "true", "yes") or env_name != "production":
        # use SQLITE_URL if provided, otherwise default to a local file
        DATABASE_URL = os.getenv("SQLITE_URL", "sqlite:///./dev.db")
        import warnings

        warnings.warn(
            f"DATABASE_URL not provided; falling back to SQLite ({DATABASE_URL}). "
            "This fallback is intended for local development only.",
            UserWarning,
        )
    else:
        raise RuntimeError(
            "DATABASE_URL is not set. Provide it via environment variable or --env-file when running the container. "
            "Example: postgresql://cosign:Cosign2025@167.71.200.141:5432/dbname"
        )

# create engine
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Trả về generator session DB để dùng làm dependency trong FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()