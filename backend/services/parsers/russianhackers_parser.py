import httpx
from typing import List, Dict
from datetime import datetime
from bs4 import BeautifulSoup
from backend.services.parsers.base_parser import BaseParser
import re


class RussianHackersParser(BaseParser):
    """Parser for https://russianhackers.org/"""

    def __init__(self):
        super().__init__("russianhackers.org")
        self.base_url = "https://russianhackers.org"
        self.timeout = 30

    async def parse(self) -> List[Dict]:
        """Parse hackathons from https://russianhackers.org/"""
        hackathons = []
        try:
            self.logger.info(f"Starting to parse {self.base_url}")

            async with httpx.AsyncClient() as client:
                # Try different possible paths
                urls = [
                    f"{self.base_url}",
                    f"{self.base_url}/events",
                    f"{self.base_url}/hackathons",
                    f"{self.base_url}/competitions",
                ]

                for url in urls:
                    try:
                        response = await client.get(url, timeout=self.timeout)
                        response.raise_for_status()

                        soup = BeautifulSoup(response.text, "html.parser")

                        # Find hackathon containers
                        hackathon_elements = soup.find_all("div", class_=re.compile(r"hackathon|event|card|competition", re.IGNORECASE))

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
                text = link_elem.get_text(strip=True)
                if text and len(text) > 3:  # Avoid taking small links
                    hackathon["title"] = text

        # Extract description
        desc_elem = element.find("p")
        if desc_elem:
            hackathon["description"] = desc_elem.get_text(strip=True)

        # Extract URL
        link_elem = element.find("a", href=True)
        if link_elem:
            url = link_elem["href"]
            hackathon["url"] = url if url.startswith("http") else f"{self.base_url}{url}"

        # Extract dates
        text = element.get_text()
        dates = self._extract_dates(text)
        if dates:
            hackathon.update(dates)

        # Extract location - Russian cities
        location_keywords = {
            "online": ["онлайн", "online", "удалённо", "удаленно"],
            "Moscow": ["москва", "москв", "мск"],
            "SPB": ["санкт-петербург", "спб", "питер"],
            "Kazan": ["казань", "казан"],
            "Novosibirsk": ["новосибирск"],
            "Yekaterinburg": ["екатеринбург", "екб"],
        }

        for location, keywords in location_keywords.items():
            for keyword in keywords:
                if keyword in text.lower():
                    hackathon["location"] = location
                    break
            if "location" in hackathon:
                break

        # Set format
        if any(kw in text.lower() for kw in location_keywords["online"]):
            hackathon["format"] = "online"
        else:
            hackathon["format"] = "offline"

        # Extract technologies if mentioned
        tech_keywords = ["python", "javascript", "java", "c++", "rust", "go", "react", "ai", "ml", "machine learning", "blockchain", "web3"]
        technologies = []
        for tech in tech_keywords:
            if tech in text.lower():
                technologies.append(tech.capitalize())

        if technologies:
            hackathon["technologies"] = list(set(technologies))

        hackathon["source"] = self.source_name

        return hackathon

    def _extract_dates(self, text: str) -> Dict:
        """Extract dates from text"""
        dates = {}

        # Look for date patterns
        # Pattern: DD-MM-YYYY or DD.MM.YYYY or DD/MM/YYYY
        date_pattern = r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"
        matches = re.findall(date_pattern, text)

        try:
            if matches:
                # Would parse dates more carefully here
                # This is a simplified version
                pass
        except Exception as e:
            self.logger.debug(f"Error extracting dates: {str(e)}")

        return dates
