import httpx
from typing import List, Dict
from datetime import datetime
from bs4 import BeautifulSoup
from backend.services.parsers.base_parser import BaseParser
import re


class HackathonsProParser(BaseParser):
    """Parser for https://hackathons.pro/"""

    def __init__(self):
        super().__init__("hackathons.pro")
        self.base_url = "https://hackathons.pro"
        self.timeout = 30

    async def parse(self) -> List[Dict]:
        """Parse hackathons from https://hackathons.pro/"""
        hackathons = []
        try:
            self.logger.info(f"Starting to parse {self.base_url}")

            async with httpx.AsyncClient() as client:
                # Try main page and events page
                urls = [
                    f"{self.base_url}",
                    f"{self.base_url}/events",
                    f"{self.base_url}/hackathons",
                ]

                for url in urls:
                    try:
                        response = await client.get(url, timeout=self.timeout)
                        response.raise_for_status()

                        soup = BeautifulSoup(response.text, "html.parser")

                        # Find hackathon containers
                        hackathon_elements = soup.find_all("div", class_=re.compile(r"hackathon|event|card|item", re.IGNORECASE))

                        if not hackathon_elements:
                            hackathon_elements = soup.find_all("article")

                        if not hackathon_elements:
                            hackathon_elements = soup.find_all("li", class_=re.compile(r"hackathon|event", re.IGNORECASE))

                        for element in hackathon_elements:
                            try:
                                hackathon = self._parse_hackathon_element(element)
                                if hackathon and hackathon.get("title"):
                                    hackathons.append(self.normalize_data(hackathon))
                            except Exception as e:
                                self.logger.debug(f"Error parsing hackathon element: {str(e)}")
                                continue

                        if hackathons:
                            break  # Stop if we found events

                    except Exception as e:
                        self.logger.debug(f"Error parsing {url}: {str(e)}")
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
        title_elem = element.find(["h2", "h3", "h4"])
        if title_elem:
            hackathon["title"] = title_elem.get_text(strip=True)
        else:
            # Try link as title
            link_elem = element.find("a", href=True)
            if link_elem:
                hackathon["title"] = link_elem.get_text(strip=True)

        # Extract description
        desc_elem = element.find("p")
        if desc_elem:
            hackathon["description"] = desc_elem.get_text(strip=True)

        # Extract URL
        link_elem = element.find("a", href=True)
        if link_elem:
            url = link_elem["href"]
            hackathon["url"] = url if url.startswith("http") else f"{self.base_url}{url}"

        # Extract dates - look for date patterns
        text = element.get_text()
        dates = self._extract_dates(text)
        if dates:
            hackathon.update(dates)

        # Extract location
        location_keywords = [
            "online", "москва", "спб", "санкт-петербург", "казань",
            "новосибирск", "екатеринбург", "самара", "воронеж"
        ]
        for keyword in location_keywords:
            if keyword in text.lower():
                hackathon["location"] = keyword.capitalize()
                break

        # Set format based on content
        if "online" in text.lower():
            hackathon["format"] = "online"
        elif any(city in text.lower() for city in location_keywords[1:]):
            hackathon["format"] = "offline"

        hackathon["source"] = self.source_name

        return hackathon

    def _extract_dates(self, text: str) -> Dict:
        """Extract dates from text"""
        dates = {}

        # Look for date patterns like "2024-03-15" or "15 марта"
        date_pattern = r"\d{1,2}[.-]\d{1,2}[.-]\d{2,4}"
        matches = re.findall(date_pattern, text)

        try:
            if matches:
                # Simple approach: use first date as start, second as end if available
                if len(matches) >= 1:
                    # Would parse dates more carefully here
                    pass
        except Exception as e:
            self.logger.debug(f"Error extracting dates: {str(e)}")

        return dates
