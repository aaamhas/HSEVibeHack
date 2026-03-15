import httpx
from typing import List, Dict
from datetime import datetime
from bs4 import BeautifulSoup
from backend.services.parsers.base_parser import BaseParser
import re


class XakatonRuParser(BaseParser):
    """Parser for https://хакатоны.рус"""

    def __init__(self):
        super().__init__("xakatony.ru")
        self.base_url = "https://хакатоны.рус"
        self.timeout = 30

    async def parse(self) -> List[Dict]:
        """Parse hackathons from https://хакатоны.рус"""
        hackathons = []
        try:
            self.logger.info(f"Starting to parse {self.base_url}")

            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, timeout=self.timeout)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                # Find hackathon containers - adjust selectors based on actual HTML structure
                hackathon_elements = soup.find_all("div", class_=re.compile(r"hackathon|event|card"))

                if not hackathon_elements:
                    # Try alternative selectors
                    hackathon_elements = soup.find_all("article")

                if not hackathon_elements:
                    self.logger.warning(f"No hackathon elements found on {self.base_url}")
                    return hackathons

                for element in hackathon_elements:
                    try:
                        hackathon = self._parse_hackathon_element(element)
                        if hackathon and hackathon.get("title"):
                            hackathons.append(self.normalize_data(hackathon))
                    except Exception as e:
                        self.logger.debug(f"Error parsing hackathon element: {str(e)}")
                        continue

                self.log_success(len(hackathons))

        except httpx.TimeoutException:
            self.log_error(Exception(f"Request timeout to {self.base_url}"))
        except Exception as e:
            self.log_error(e, f"Failed to parse {self.base_url}")

        return hackathons

    def _parse_hackathon_element(self, element) -> Dict:
        """Parse individual hackathon element"""
        hackathon = {}

        # Extract title
        title_elem = element.find("h2") or element.find("h3") or element.find("a")
        if title_elem:
            hackathon["title"] = title_elem.get_text(strip=True)

        # Extract description
        desc_elem = element.find("p")
        if desc_elem:
            hackathon["description"] = desc_elem.get_text(strip=True)

        # Extract URL
        link_elem = element.find("a", href=True)
        if link_elem:
            url = link_elem["href"]
            hackathon["url"] = url if url.startswith("http") else f"{self.base_url}{url}"

        # Extract dates - try common patterns
        text = element.get_text()
        dates = self._extract_dates(text)
        if dates:
            hackathon.update(dates)

        # Extract location
        location_match = re.search(r"(Москва|СПб|Санкт-Петербург|Казань|Новосибирск|онлайн|Online)", text, re.IGNORECASE)
        if location_match:
            hackathon["location"] = location_match.group(1)

        hackathon["source"] = self.source_name

        return hackathon

    def _extract_dates(self, text: str) -> Dict:
        """Extract dates from text"""
        dates = {}

        # Try to find date patterns (Russian and English formats)
        # Pattern: ДД месяца or MM-DD
        date_pattern = r"\d{1,2}\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"

        try:
            # For more accurate parsing, would need more sophisticated date extraction
            # This is a simplified version
            if "по" in text or "-" in text:
                # Try to extract range
                parts = re.split(r"по|-", text)
                if len(parts) >= 2:
                    # Would parse dates here
                    pass
        except Exception as e:
            self.logger.debug(f"Error extracting dates: {str(e)}")

        return dates
