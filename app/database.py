import os
import shutil
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

def resolve_database_url(database_url: str) -> str:
    # On Linux/Render/Docker, use the database path directly
    if os.name != "nt":
        return database_url

    if not database_url.startswith("sqlite:///./"):
        return database_url

    source_path = Path.cwd() / database_url.removeprefix("sqlite:///./")
    data_root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "SportsPitch"
    target_path = data_root / source_path.name
    try:
        data_root.mkdir(parents=True, exist_ok=True)
        if source_path.exists() and not target_path.exists():
            shutil.copy2(source_path, target_path)
        return f"sqlite:///{target_path.as_posix()}"
    except Exception:
        return database_url


database_url = resolve_database_url(settings.DATABASE_URL)
connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}

engine = create_engine(database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
