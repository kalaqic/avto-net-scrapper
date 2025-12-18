"""
API Server Entry Point - User-based persistent scraping system
Run this file to start the FastAPI server with background worker
"""
import asyncio
import signal
import sys
import os
from contextlib import asynccontextmanager
from src.database.models import Database
from src.api.worker import ScrapingWorker
from src.shared.log import logger
import uvicorn

# Import app after setting up worker (to avoid circular imports)
from src.api.main import app

# Initialize database
db = Database(db_path=os.getenv("DB_PATH", "data/scraper.db"))

# Initialize worker
scrape_interval = int(os.getenv("SCRAPE_INTERVAL", "60"))  # Default 60 seconds
worker = ScrapingWorker(db, scrape_interval=scrape_interval)

# Global worker task
worker_task = None


@asynccontextmanager
async def lifespan(app_instance):
    """Lifespan context manager for FastAPI"""
    global worker_task
    
    # Startup
    logger.info("Starting background scraping worker...")
    worker_task = asyncio.create_task(worker.start())
    
    yield
    
    # Shutdown
    logger.info("Shutting down worker...")
    worker.stop()
    if worker_task:
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass


# Attach lifespan to app
app.router.lifespan_context = lifespan


def signal_handler(sig, frame):
    """Handle shutdown signals"""
    logger.info("Shutdown signal received. Stopping worker...")
    worker.stop()
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"Starting API server on {host}:{port}")
    logger.info(f"Scrape interval: {scrape_interval} seconds")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
