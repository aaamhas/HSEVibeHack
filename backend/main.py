from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from backend.database import init_db
from backend.init_technologies import init_technologies
from backend.routers import hackathons

load_dotenv()

app = FastAPI(
    title="VibeHack API",
    description="Hackathon discovery platform with AI recommendations",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup initialization
@app.on_event("startup")
async def startup():
    """Initialize database and technologies"""
    init_db()
    init_technologies()


# Include routers
app.include_router(hackathons.router)


@app.get("/")
async def root():
    return {"message": "Welcome to VibeHack API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import logging

from backend.database import init_db
from backend.init_technologies import init_technologies
from backend.routers import hackathons
from backend.config.logging_config import setup_logging, get_logger

load_dotenv()

# Initialize logging
setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="VibeHack API",
    description="Hackathon discovery platform with AI recommendations",
    version="1.0.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup initialization
@app.on_event("startup")
async def startup():
    """Initialize database and technologies"""
    try:
        logger.info("Starting application initialization...")
        init_db()
        logger.info("Database initialized successfully")
        init_technologies()
        logger.info("Technologies initialized successfully")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}", exc_info=True)
        raise


# Include routers
app.include_router(hackathons.router)


@app.get("/")
async def root():
    return {"message": "Welcome to VibeHack API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

