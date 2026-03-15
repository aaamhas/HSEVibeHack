from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
from backend.models import Hackathon
from backend.config.logging_config import get_logger
from backend.services.parsers.xakatonru_parser import XakatonRuParser
from backend.services.parsers.hackathonspro_parser import HackathonsProParser
from backend.services.parsers.russianhackers_parser import RussianHackersParser

logger = get_logger(__name__)


class HackathonService:
    """Service for managing hackathon data"""

    def __init__(self):
        """Initialize service with all available parsers"""
        self.parsers = [
            XakatonRuParser(),
            HackathonsProParser(),
            RussianHackersParser(),
        ]

    async def run_all_parsers(self, db: Session) -> Dict:
        """
        Run all parsers and save new hackathons to database.

        Args:
            db: Database session

        Returns:
            Summary dict with stats
        """
        summary = {
            "total_found": 0,
            "total_added": 0,
            "duplicates_skipped": 0,
            "errors": [],
            "parser_results": []
        }

        try:
            logger.info("Starting all hackathon parsers")

            for parser in self.parsers:
                try:
                    logger.info(f"Running parser: {parser.source_name}")

                    # Run parser (async)
                    hackathons = await parser.parse()

                    added_count = 0
                    duplicate_count = 0

                    for hackathon_data in hackathons:
                        # Check if hackathon already exists (by title and source)
                        existing = db.query(Hackathon).filter(
                            Hackathon.title == hackathon_data.get("title"),
                            Hackathon.source == hackathon_data.get("source")
                        ).first()

                        if existing:
                            logger.debug(f"Duplicate hackathon skipped: {hackathon_data.get('title')}")
                            duplicate_count += 1
                            continue

                        # Create new hackathon
                        try:
                            db_hackathon = Hackathon(**hackathon_data)
                            db.add(db_hackathon)
                            db.commit()
                            db.refresh(db_hackathon)
                            added_count += 1
                            logger.debug(f"Added hackathon: {db_hackathon.title}")
                        except Exception as e:
                            logger.error(f"Error saving hackathon: {str(e)}", exc_info=True)
                            db.rollback()
                            continue

                    summary["total_found"] += len(hackathons)
                    summary["total_added"] += added_count
                    summary["duplicates_skipped"] += duplicate_count

                    parser_result = {
                        "parser": parser.source_name,
                        "found": len(hackathons),
                        "added": added_count,
                        "duplicates": duplicate_count
                    }
                    summary["parser_results"].append(parser_result)

                    logger.info(
                        f"Parser {parser.source_name}: found={len(hackathons)}, "
                        f"added={added_count}, duplicates={duplicate_count}"
                    )

                except Exception as e:
                    logger.error(f"Error in parser {parser.source_name}: {str(e)}", exc_info=True)
                    summary["errors"].append({
                        "parser": parser.source_name,
                        "error": str(e)
                    })

            logger.info(f"Parsing complete. Summary: {summary}")

        except Exception as e:
            logger.error(f"Critical error in run_all_parsers: {str(e)}", exc_info=True)
            summary["errors"].append({
                "parser": "general",
                "error": str(e)
            })

        return summary

    def get_parser_sources(self) -> List[str]:
        """Get list of available parser sources"""
        return [parser.source_name for parser in self.parsers]
