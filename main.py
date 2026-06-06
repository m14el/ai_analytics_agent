"""
AI Analytics Agent — Main Application Entry Point
FastAPI application with dashboard, API, and background scheduler.
"""
import logging
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from models.database import init_db
from dashboard.routes import router as dashboard_router, run_etl_pipeline
from scheduler.jobs import start_scheduler, stop_scheduler

# ── Logging ─────────────────────────────────────────────────
LOG_LEVEL = logging.DEBUG if settings.app_debug else logging.INFO
if settings.app_env == "production":
    LOG_LEVEL = logging.WARNING

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)-7s | %(name)-25s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
# Suppress noisy SQLAlchemy logs
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logger = logging.getLogger("aaa")

# ── App start time for uptime tracking ──────────────────────
_start_time: float = 0.0


# ── Lifespan ────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _start_time
    _start_time = time.time()
    logger.info("AI Analytics Agent starting (env=%s)...", settings.app_env)
    init_db()
    logger.info("Database initialized")

    # Run initial ETL
    await run_etl_pipeline()

    # Start scheduler
    start_scheduler()

    yield

    stop_scheduler()
    logger.info("AI Analytics Agent stopped")


# ── App ─────────────────────────────────────────────────────
app = FastAPI(
    title="AI Analytics Agent",
    description="AI-агент аналитики прибыльности проектов, стеков и процессов разработки",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.app_debug else None,
    redoc_url="/redoc" if settings.app_debug else None,
)

# ── Middleware ──────────────────────────────────────────────
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Trusted Hosts (production only)
if settings.app_env == "production" and settings.allowed_hosts != "*":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts_list,
    )


# ── Global Exception Handler ───────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    # Never expose stack traces in production
    detail = str(exc) if settings.app_debug else "Internal server error"
    return JSONResponse(status_code=500, content={"detail": detail})


# ── Health Check ────────────────────────────────────────────
@app.get("/health", tags=["system"])
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.app_env,
        "uptime_seconds": round(time.time() - _start_time, 1) if _start_time else 0,
    }


# Static files
static_dir = Path(__file__).parent / "dashboard" / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Routes
app.include_router(dashboard_router)


# ── Run ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
    )
