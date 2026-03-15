from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
from backend.config.logging_config import get_logger

logger = get_logger(__name__)


class BaseParser(ABC):
    """Base class for hackathon parsers"""

    def __init__(self, source_name: str):
        """Initialize parser with source name"""
        self.source_name = source_name
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def parse(self) -> List[Dict]:
        """
        Parse hackathons from the source.

        Returns:
            List of hackathon dictionaries with keys:
            - title: str
            - description: str (optional)
            - start_date: datetime (optional)
            - end_date: datetime (optional)
            - registration_deadline: datetime (optional)
            - url: str
            - location: str (optional)
            - source: str (set to self.source_name)
            - technologies: List[str] (optional)
        """
        pass

    def normalize_data(self, data: Dict) -> Dict:
        """
        Normalize parsed data to match Hackathon schema.

        Args:
            data: Raw parsed data

        Returns:
            Normalized hackathon data
        """
        return {
            "title": data.get("title", "").strip(),
            "description": data.get("description", "").strip() if data.get("description") else None,
            "start_date": data.get("start_date"),
            "end_date": data.get("end_date"),
            "registration_deadline": data.get("registration_deadline"),
            "format": data.get("format", "online"),
            "url": data.get("url", "").strip() if data.get("url") else None,
            "location": data.get("location", "").strip() if data.get("location") else None,
            "source": self.source_name,
            "technologies": data.get("technologies", []) or [],
        }

    def log_success(self, count: int):
        """Log successful parsing"""
        self.logger.info(f"Successfully parsed {count} hackathons from {self.source_name}")

    def log_error(self, error: Exception, context: str = ""):
        """Log parsing error"""
        self.logger.error(
            f"Error parsing from {self.source_name}: {str(error)} {context}",
            exc_info=True
        )
