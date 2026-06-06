"""
AI Analytics Agent — Scheduled Jobs
APScheduler-based ETL job scheduling.
"""
import asyncio
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from config import settings

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def _run_etl_sync():
    """Synchronous wrapper for the async ETL pipeline."""
    from dashboard.routes import run_etl_pipeline
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(run_etl_pipeline())
    finally:
        loop.close()


def start_scheduler():
    """Start the background scheduler if enabled."""
    if not settings.etl_schedule_enabled:
        logger.info("Scheduler disabled (ETL_SCHEDULE_ENABLED=false)")
        return

    scheduler.add_job(
        _run_etl_sync,
        "interval",
        hours=settings.etl_schedule_hours,
        id="etl_pipeline",
        name="ETL Pipeline",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Scheduler started: ETL every {settings.etl_schedule_hours}h")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
