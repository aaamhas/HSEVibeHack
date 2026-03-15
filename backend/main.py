import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

from backend.database import init_db
from backend.init_technologies import init_technologies
from backend.routers import hackathons
from backend.services.hackathon_updater import HackathonUpdater
from backend.config.logging_config import setup_logging, get_logger

load_dotenv()
setup_logging()
logger = get_logger(__name__)

scheduler = AsyncIOScheduler()


def run_scrape_and_enrich():
    """Scrape hackathons using existing parsers + enrich with Qwen2."""
    try:
        # Use existing HackathonService parsers
        from backend.hackathon_service import HackathonService
        from backend.database import SessionLocal
        import asyncio

        service = HackathonService()
        db = SessionLocal()
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            summary = loop.run_until_complete(service.run_all_parsers(db))
            loop.close()
            logger.info(f"Scraping completed: {summary}")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error during scraping: {e}", exc_info=True)

    # Enrich hackathon data with Qwen2
    try:
        updater = HackathonUpdater()
        updater.run_daily_update()
    except Exception as e:
        logger.error(f"Error during enrichment: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting application initialization...")
    init_db()
    logger.info("Database initialized successfully")
    init_technologies()
    logger.info("Technologies initialized successfully")

    # Run scraping + enrichment in background thread (non-blocking)
    logger.info("Starting background scraping and enrichment...")
    bg_thread = threading.Thread(target=run_scrape_and_enrich, daemon=True)
    bg_thread.start()

    # Schedule daily at 03:00
    scheduler.add_job(
        lambda: threading.Thread(target=run_scrape_and_enrich, daemon=True).start(),
        "cron", hour=3, minute=0
    )
    scheduler.start()
    logger.info("Daily scraping + enrichment scheduled at 03:00")

    yield

    # Shutdown
    scheduler.shutdown()


app = FastAPI(
    title="VibeHack API",
    description="Hackathon discovery platform with AI recommendations",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(hackathons.router)


@app.get("/")
async def root():
    return {"message": "Welcome to VibeHack API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/admin/scrape-hackathons")
async def trigger_scraping():
    """Manually trigger hackathon scraping + enrichment in background."""
    bg = threading.Thread(target=run_scrape_and_enrich, daemon=True)
    bg.start()
    return {"message": "Scraping started in background"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
