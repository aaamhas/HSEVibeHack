import os
import json
import re
from datetime import datetime
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import ollama

from backend.database import SessionLocal
from backend.models import Hackathon, Technology

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}


class HackathonScraper:
    """Scrapes hackathons from hackathons.pro and хакатоны.рус, uses Qwen2 for deduplication."""

    # Tilda feeds API for hackathons.pro
    HACKATHONS_PRO_FEED_URL = (
        "https://feeds.tildacdn.com/api/getfeed/"
        "?feeduid=131632209651-986950497851&recid=442995264&c=1&size=50&slice=1"
    )
    HACKATHONS_PRO_BASE = "https://hackathons.pro"

    # хакатоны.рус
    HACKATHONS_RUS_URL = "https://xn--80aa3anexr8c.xn--p1acf/"
    HACKATHONS_RUS_FEED_URL = (
        "https://feeds.tildacdn.com/api/getfeed/"
        "?feeduid=617755803461&recid=488755787&c=1&size=50&slice=1"
    )

    def __init__(self):
        self.ollama_client = ollama.Client(host=OLLAMA_BASE_URL)
        self.model_name = "qwen2"

    def run_scraping(self):
        """Main entry point: scrape all sources and save to DB."""
        db = SessionLocal()
        try:
            existing_hackathons = db.query(Hackathon).all()
            existing_titles = [h.title for h in existing_hackathons]

            # Scrape hackathons.pro
            pro_hackathons = self._scrape_hackathons_pro()
            print(f"[Scraper] hackathons.pro: found {len(pro_hackathons)} hackathons")

            # Scrape хакатоны.рус
            rus_hackathons = self._scrape_hackathons_rus()
            print(f"[Scraper] хакатоны.рус: found {len(rus_hackathons)} hackathons")

            all_scraped = pro_hackathons + rus_hackathons

            # Deduplicate using Qwen2
            new_hackathons = self._deduplicate(all_scraped, existing_titles)
            print(f"[Scraper] After deduplication: {len(new_hackathons)} new hackathons")

            # Save to DB
            saved = 0
            for h_data in new_hackathons:
                hackathon = self._create_hackathon(db, h_data)
                if hackathon:
                    saved += 1

            db.commit()
            print(f"[Scraper] Saved {saved} new hackathons to database")

        except Exception as e:
            db.rollback()
            print(f"[Scraper] Error during scraping: {e}")
        finally:
            db.close()

    def _scrape_hackathons_pro(self) -> List[Dict]:
        """Scrape hackathons from hackathons.pro via Tilda feeds API."""
        hackathons = []
        try:
            resp = requests.get(self.HACKATHONS_PRO_FEED_URL, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            for post in data.get("posts", []):
                title = post.get("title", "").strip()
                if not title:
                    continue

                descr = post.get("descr", "").strip()
                url = post.get("url", "")
                if url and not url.startswith("http"):
                    url = f"{self.HACKATHONS_PRO_BASE}{url}"

                date_str = post.get("date", "")

                # Try to get more details from the post page
                details = self._fetch_post_details_pro(url) if url else {}

                hackathons.append({
                    "title": title,
                    "description": details.get("description") or descr,
                    "start_date": details.get("start_date"),
                    "end_date": details.get("end_date"),
                    "registration_deadline": details.get("registration_deadline"),
                    "format": details.get("format", "online"),
                    "url": details.get("register_url") or url,
                    "location": details.get("location"),
                    "source": "hackathons.pro",
                    "prize": details.get("prize"),
                })

        except Exception as e:
            print(f"[Scraper] Error scraping hackathons.pro: {e}")

        return hackathons

    def _fetch_post_details_pro(self, url: str) -> Dict:
        """Fetch and parse individual hackathon page from hackathons.pro using Qwen2."""
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # Extract text content from the post
            text_blocks = soup.find_all(["p", "div", "span", "li", "h1", "h2", "h3"])
            page_text = "\n".join(
                block.get_text(strip=True) for block in text_blocks if block.get_text(strip=True)
            )
            # Limit text to avoid huge prompts
            page_text = page_text[:3000]

            return self._extract_details_with_qwen(page_text)

        except Exception as e:
            print(f"[Scraper] Error fetching post {url}: {e}")
            return {}

    def _scrape_hackathons_rus(self) -> List[Dict]:
        """Scrape hackathons from хакатоны.рус."""
        hackathons = []

        # Try Tilda feeds API first
        try:
            resp = requests.get(self.HACKATHONS_RUS_FEED_URL, headers=HEADERS, timeout=30)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    for post in data.get("posts", []):
                        title = post.get("title", "").strip()
                        if not title:
                            continue

                        descr = post.get("descr", "").strip()
                        url = post.get("url", "")

                        hackathons.append({
                            "title": title,
                            "description": descr,
                            "start_date": None,
                            "end_date": None,
                            "registration_deadline": None,
                            "format": "online",
                            "url": url,
                            "location": None,
                            "source": "хакатоны.рус",
                            "prize": None,
                        })
                    return hackathons
                except (json.JSONDecodeError, ValueError):
                    pass
        except Exception:
            pass

        # Fallback: parse HTML directly
        try:
            resp = requests.get(self.HACKATHONS_RUS_URL, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            # Look for feed post elements
            posts = soup.find_all("div", class_="t-feed__post")
            for post in posts:
                title_el = post.find(class_="t-feed__post-title")
                descr_el = post.find(class_="t-feed__post-descr")
                link_el = post.find("a", href=True)

                title = title_el.get_text(strip=True) if title_el else ""
                if not title:
                    continue

                hackathons.append({
                    "title": title,
                    "description": descr_el.get_text(strip=True) if descr_el else "",
                    "start_date": None,
                    "end_date": None,
                    "registration_deadline": None,
                    "format": "online",
                    "url": link_el["href"] if link_el else "",
                    "location": None,
                    "source": "хакатоны.рус",
                    "prize": None,
                })

        except Exception as e:
            print(f"[Scraper] Error scraping хакатоны.рус: {e}")

        return hackathons

    def _extract_details_with_qwen(self, page_text: str) -> Dict:
        """Use Qwen2 to extract structured hackathon details from page text."""
        prompt = f"""Extract hackathon details from this text. Return ONLY valid JSON:
{{
    "description": "brief description of the hackathon (2-3 sentences)",
    "start_date": "YYYY-MM-DD or null",
    "end_date": "YYYY-MM-DD or null",
    "registration_deadline": "YYYY-MM-DD or null",
    "format": "online/offline/hybrid",
    "location": "city/country or null",
    "register_url": "registration URL or null",
    "prize": "prize description or null"
}}

Text:
{page_text}

Return ONLY the JSON object."""

        try:
            response = self.ollama_client.generate(
                model=self.model_name,
                prompt=prompt,
                stream=False,
            )

            raw = response.get("response", "").strip()
            return self._extract_json(raw)
        except Exception as e:
            print(f"[Scraper] Qwen extraction error: {e}")
            return {}

    def _deduplicate(self, scraped: List[Dict], existing_titles: List[str]) -> List[Dict]:
        """Use Qwen2 to detect duplicates between scraped hackathons and existing DB entries."""
        if not scraped:
            return []

        # First pass: exact title match
        candidates = []
        for h in scraped:
            if h["title"] not in existing_titles:
                candidates.append(h)

        if not candidates or not existing_titles:
            return candidates

        # Second pass: use Qwen2 for fuzzy deduplication
        # Process in batches to avoid prompt size limits
        deduplicated = []
        batch_size = 10

        for i in range(0, len(candidates), batch_size):
            batch = candidates[i:i + batch_size]
            batch_titles = [h["title"] for h in batch]

            # Only compare against a sample of existing titles to keep prompt manageable
            sample_existing = existing_titles[:50]

            prompt = f"""You are a deduplication assistant. Compare new hackathon titles against existing ones and identify duplicates.
Two hackathons are duplicates if they are the same event (even if titles differ slightly, e.g. abbreviations, different word order, translated names).

Existing hackathons in database:
{json.dumps(sample_existing, ensure_ascii=False)}

New hackathons to check:
{json.dumps(batch_titles, ensure_ascii=False)}

Return ONLY a JSON array of indices (0-based) of NEW hackathons that are NOT duplicates.
Example: [0, 2, 4] means items at index 0, 2, 4 are unique.
Return ONLY the JSON array."""

            try:
                response = self.ollama_client.generate(
                    model=self.model_name,
                    prompt=prompt,
                    stream=False,
                )

                raw = response.get("response", "").strip()
                # Extract array
                arr_match = re.search(r"\[[\d\s,]*\]", raw)
                if arr_match:
                    unique_indices = json.loads(arr_match.group(0))
                    for idx in unique_indices:
                        if isinstance(idx, int) and 0 <= idx < len(batch):
                            deduplicated.append(batch[idx])
                else:
                    # If Qwen fails, keep all candidates
                    deduplicated.extend(batch)

            except Exception as e:
                print(f"[Scraper] Deduplication error: {e}")
                deduplicated.extend(batch)

        return deduplicated

    def _create_hackathon(self, db, h_data: Dict) -> Optional[Hackathon]:
        """Create a Hackathon record in the database."""
        try:
            hackathon = Hackathon(
                title=h_data["title"],
                description=h_data.get("description"),
                start_date=self._parse_date(h_data.get("start_date")),
                end_date=self._parse_date(h_data.get("end_date")),
                registration_deadline=self._parse_date(h_data.get("registration_deadline")),
                format=h_data.get("format", "online"),
                url=h_data.get("url"),
                location=h_data.get("location"),
                source=h_data.get("source"),
                prize=h_data.get("prize"),
            )
            db.add(hackathon)
            return hackathon
        except Exception as e:
            print(f"[Scraper] Error creating hackathon '{h_data.get('title')}': {e}")
            return None

    def _parse_date(self, date_val) -> Optional[datetime]:
        """Parse date from string or return None."""
        if not date_val or date_val == "null":
            return None
        if isinstance(date_val, datetime):
            return date_val
        try:
            return datetime.fromisoformat(str(date_val))
        except (ValueError, TypeError):
            pass
        # Try common formats
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M", "%d.%m.%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(str(date_val), fmt)
            except (ValueError, TypeError):
                continue
        return None

    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from LLM response."""
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if json_match:
            text = json_match.group(1).strip()

        json_match = re.search(r"\{[\s\S]*\}", text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        return {}
