import logging
import logging.handlers
import os
from pathlib import Path

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOG_FILE = LOGS_DIR / "vibehack.log"
ERROR_LOG_FILE = LOGS_DIR / "vibehack_errors.log"

# Define log format
LOG_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging():
    """Configure centralized logging for the application."""

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatters
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # Console handler (INFO level)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # File handler (DEBUG level - all logs)
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE,
        maxBytes=10_000_000,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Error file handler (ERROR level - only errors)
    error_handler = logging.handlers.RotatingFileHandler(
        ERROR_LOG_FILE,
        maxBytes=10_000_000,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)

    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(error_handler)

    # Set logging level for specific modules
    logging.getLogger("sqlalchemy").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.INFO)

    root_logger.info("Logging system initialized")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)
