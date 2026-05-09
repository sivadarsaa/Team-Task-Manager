from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_settings


def normalize_database_url(raw_url: str) -> str:
    if raw_url.startswith("postgres://"):
        return raw_url.replace("postgres://", "postgresql+psycopg://", 1)
    if raw_url.startswith("postgresql://") and "+psycopg" not in raw_url:
        return raw_url.replace("postgresql://", "postgresql+psycopg://", 1)
    if raw_url.startswith("sqlite:///./"):
        relative_path = raw_url.removeprefix("sqlite:///./")
        absolute_path = (Path.cwd() / relative_path).resolve()
        return f"sqlite:///{absolute_path.as_posix()}"
    if raw_url.startswith("sqlite:///"):
        sqlite_path = Path(raw_url.removeprefix("sqlite:///")).expanduser()
        return f"sqlite:///{sqlite_path.as_posix()}"
    return raw_url


def ensure_database_storage(raw_url: str) -> None:
    if not raw_url.startswith("sqlite:///"):
        return

    sqlite_path = Path(raw_url.removeprefix("sqlite:///"))
    sqlite_path.parent.mkdir(parents=True, exist_ok=True)


settings = get_settings()
database_url = normalize_database_url(settings.database_url)

engine_kwargs = {
    "pool_pre_ping": True,
}
if database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_recycle"] = 300

engine = create_engine(database_url, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)
Base = declarative_base()
