import os
import json
import re
from datetime import datetime
from typing import List, Dict, Optional
from dotenv import load_dotenv
import ollama

from backend.database import SessionLocal
from backend.models import Hackathon, Technology

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


class HackathonUpdater:
    """Service that uses Qwen2 to enrich hackathon data in the database daily."""

    def __init__(self):
        self.ollama_client = ollama.Client(host=OLLAMA_BASE_URL)
        self.model_name = "qwen2"

    def run_daily_update(self):
        """Main entry point: enrich all hackathons that have missing fields."""
        db = SessionLocal()
        try:
            hackathons = db.query(Hackathon).all()
            updated_count = 0

            for hackathon in hackathons:
                if self._needs_enrichment(hackathon):
                    enriched = self._enrich_hackathon(hackathon)
                    if enriched:
                        updated_count += 1

            db.commit()
            print(f"[HackathonUpdater] Updated {updated_count}/{len(hackathons)} hackathons")
        except Exception as e:
            db.rollback()
            print(f"[HackathonUpdater] Error during daily update: {e}")
        finally:
            db.close()

    def _needs_enrichment(self, hackathon: Hackathon) -> bool:
        """Check if hackathon has missing fields that can be enriched."""
        return any([
            not hackathon.theme,
            not hackathon.skill_level,
            hackathon.team_size_min is None,
            hackathon.team_size_max is None,
            not hackathon.prize,
            hackathon.duration_hours is None,
        ])

    def _enrich_hackathon(self, hackathon: Hackathon) -> bool:
        """Use Qwen2 to extract missing fields from hackathon title and description."""
        text = f"{hackathon.title or ''}\n{hackathon.description or ''}"
        if not text.strip():
            return False

        tech_names = [t.name for t in hackathon.technologies]

        prompt = f"""You are a JSON extraction assistant. Analyze this hackathon and extract missing metadata.

Hackathon title: {hackathon.title or 'N/A'}
Description: {hackathon.description or 'N/A'}
Technologies: {', '.join(tech_names) if tech_names else 'N/A'}
Start date: {hackathon.start_date or 'N/A'}
End date: {hackathon.end_date or 'N/A'}
Format: {hackathon.format or 'N/A'}
Location: {hackathon.location or 'N/A'}

Extract the following. Return ONLY valid JSON:
{{
    "theme": "main theme: fintech, ai, gamedev, healthcare, education, cybersecurity, social, sustainability, web3, iot, general, or null if unclear",
    "skill_level": "beginner/intermediate/advanced/any or null",
    "team_size_min": number or null (minimum team size),
    "team_size_max": number or null (maximum team size),
    "prize": "brief prize description or null (e.g. '$10000', 'internship at Google', 'certificates')",
    "duration_hours": number or null (calculate from start/end dates if available, or estimate from description)
}}

Rules:
- Only fill fields you can confidently determine from the provided info
- Return null for uncertain fields
- Return ONLY the JSON object"""

        try:
            response = self.ollama_client.generate(
                model=self.model_name,
                prompt=prompt,
                stream=False,
            )

            raw = response.get("response", "").strip()
            data = self._extract_json(raw)
            if not data:
                return False

            return self._apply_enrichment(hackathon, data)

        except Exception as e:
            print(f"[HackathonUpdater] Error enriching hackathon {hackathon.id}: {e}")
            return False

    def _extract_json(self, text: str) -> Optional[Dict]:
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
        return None

    def _apply_enrichment(self, hackathon: Hackathon, data: Dict) -> bool:
        """Apply extracted data to hackathon, only filling empty fields."""
        changed = False

        if not hackathon.theme and data.get("theme") and data["theme"] != "null":
            hackathon.theme = data["theme"]
            changed = True

        if not hackathon.skill_level and data.get("skill_level") and data["skill_level"] != "null":
            if data["skill_level"] in ("beginner", "intermediate", "advanced", "any"):
                hackathon.skill_level = data["skill_level"]
                changed = True

        if hackathon.team_size_min is None and data.get("team_size_min") and data["team_size_min"] != "null":
            try:
                hackathon.team_size_min = int(data["team_size_min"])
                changed = True
            except (ValueError, TypeError):
                pass

        if hackathon.team_size_max is None and data.get("team_size_max") and data["team_size_max"] != "null":
            try:
                hackathon.team_size_max = int(data["team_size_max"])
                changed = True
            except (ValueError, TypeError):
                pass

        if not hackathon.prize and data.get("prize") and data["prize"] != "null":
            hackathon.prize = data["prize"]
            changed = True

        if hackathon.duration_hours is None and data.get("duration_hours") and data["duration_hours"] != "null":
            try:
                hackathon.duration_hours = int(data["duration_hours"])
                changed = True
            except (ValueError, TypeError):
                pass

        return changed
