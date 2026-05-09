from contextlib import asynccontextmanager
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from app.config import get_settings
from app.database import Base, database_url, engine, ensure_database_storage
from app.routers import activity, auth, dashboard, projects, users


logger = logging.getLogger(__name__)


def run_startup_migrations() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    if "users" not in table_names:
        return

    columns = {column["name"] for column in inspector.get_columns("users")}
    with engine.begin() as connection:
        if "role" not in columns:
            connection.exec_driver_sql("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'employee'")

        legacy_admin_count = connection.execute(text("SELECT COUNT(*) FROM users WHERE role = 'admin'")).scalar_one()
        legacy_member_count = connection.execute(text("SELECT COUNT(*) FROM users WHERE role = 'member'")).scalar_one()
        if legacy_admin_count:
            connection.execute(text("UPDATE users SET role = 'manager' WHERE role = 'admin'"))
        if legacy_member_count:
            connection.execute(text("UPDATE users SET role = 'employee' WHERE role = 'member'"))

        manager_count = connection.execute(text("SELECT COUNT(*) FROM users WHERE role = 'manager'")).scalar_one()
        if manager_count == 0:
            first_user_id = connection.execute(text("SELECT id FROM users ORDER BY created_at ASC, id ASC LIMIT 1")).scalar()
            if first_user_id is not None:
                connection.execute(text("UPDATE users SET role = 'manager' WHERE id = :user_id"), {"user_id": first_user_id})


@asynccontextmanager
async def lifespan(_: FastAPI):
    ensure_database_storage(database_url)
    Base.metadata.create_all(bind=engine)
    run_startup_migrations()
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(GZipMiddleware, minimum_size=1024)
if settings.resolved_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.resolved_cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

static_dir = Path("app/static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
spa_index = static_dir / "spa" / "index.html"

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(dashboard.router)
app.include_router(users.router)
app.include_router(activity.router)


@app.get("/")
def index():
    if spa_index.exists():
        return FileResponse(spa_index)
    return JSONResponse({"name": settings.app_name, "status": "ok", "docs": "/docs"})


@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        logger.exception("Healthcheck failed")
        raise HTTPException(status_code=503, detail="Database unavailable.") from exc

    return {
        "status": "ok",
        "app": settings.app_name,
        "database": "ok",
        "spa": spa_index.exists(),
    }


@app.get("/{full_path:path}")
def spa_fallback(full_path: str):
    if full_path.startswith("api/") or full_path.startswith("static/"):
        return JSONResponse({"detail": "Not found."}, status_code=404)
    if spa_index.exists():
        return FileResponse(spa_index)
    return JSONResponse({"detail": "Frontend build not found."}, status_code=404)
