import os
import json
import re
from typing import List, Dict, Set, Optional, Tuple
from datetime import datetime
from sentence_transformers import SentenceTransformer
import numpy as np
from dotenv import load_dotenv
import ollama
from backend.config.logging_config import get_logger

load_dotenv()

logger = get_logger(__name__)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


class ParsedQuery:
    """Structured representation of parsed user query"""

    def __init__(self):
        self.technologies: List[str] = []
        self.date_from: Optional[datetime] = None
        self.date_to: Optional[datetime] = None
        self.format: Optional[str] = None
        self.location: Optional[str] = None
        self.skill_level: Optional[str] = None
        self.theme: Optional[str] = None
        self.team_size: Optional[int] = None
        self.prize: Optional[str] = None
        self.duration_hours: Optional[int] = None
        self.other: Optional[str] = None
        self.raw_query: str = ""

    def to_dict(self) -> Dict:
        return {
            "technologies": self.technologies,
            "date_from": self.date_from.isoformat() if self.date_from else None,
            "date_to": self.date_to.isoformat() if self.date_to else None,
            "format": self.format,
            "location": self.location,
            "skill_level": self.skill_level,
            "theme": self.theme,
            "team_size": self.team_size,
            "prize": self.prize,
            "duration_hours": self.duration_hours,
            "other": self.other,
            "raw_query": self.raw_query,
        }

    def get_missing_fields(self) -> List[str]:
        missing = []
        if not self.technologies:
            missing.append("technologies")
        if not self.date_from and not self.date_to:
            missing.append("dates")
        if not self.format:
            missing.append("format")
        if not self.location:
            missing.append("location")
        if not self.skill_level:
            missing.append("skill_level")
        if not self.theme:
            missing.append("theme")
        if not self.team_size:
            missing.append("team_size")
        if not self.prize:
            missing.append("prize")
        if not self.duration_hours:
            missing.append("duration_hours")
        return missing


class AIRecommender:
    def __init__(self):
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.ollama_client = ollama.Client(host=OLLAMA_BASE_URL)
        self.model_name = "qwen2"
        self.recommended_hackathons: Set[int] = set()

    def parse_user_query(self, query: str) -> ParsedQuery:
        today = datetime.utcnow()
        prompt = f"""You are a JSON extraction assistant. Extract structured information from the user's hackathon search query.
Today's date: {today.strftime('%Y-%m-%d')}

User query: "{query}"

Extract the following fields. Return ONLY valid JSON, no extra text:
{{
    "technologies": ["list of programming languages, frameworks, tools mentioned"],
    "date_from": "YYYY-MM-DD or null",
    "date_to": "YYYY-MM-DD or null",
    "format": "online/offline/hybrid or null",
    "location": "city or country or null",
    "skill_level": "beginner/intermediate/advanced or null",
    "theme": "hackathon theme like fintech, ai, gamedev, healthcare, education, cybersecurity, social, sustainability, web3 or null",
    "team_size": number or null,
    "prize": "money/internship/job/certificates or null",
    "duration_hours": number or null,
    "other": "any other important details or null"
}}

Rules:
- "spring" = March 1 to May 31, "summer" = June 1 to August 31, "autumn/fall" = Sep 1 to Nov 30, "winter" = Dec 1 to Feb 28
- "next week" = next Monday to Sunday, "next month" = first to last day of next month
- "weekend hackathon" → duration_hours: 48
- Only extract what is explicitly mentioned or clearly implied
- Return null for fields not mentioned
- Return ONLY the JSON object"""

        try:
            response = self.ollama_client.generate(model=self.model_name, prompt=prompt, stream=False)
            raw = response.get("response", "").strip()
            parsed = self._extract_json(raw)
            return self._build_parsed_query(parsed, query, today)
        except Exception as e:
            logger.error(f"Error parsing query with Qwen2: {e}", exc_info=True)
            result = ParsedQuery()
            result.raw_query = query
            return result

    def _extract_json(self, text: str) -> Dict:
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

    def _build_parsed_query(self, data: Dict, raw_query: str, today: datetime) -> ParsedQuery:
        result = ParsedQuery()
        result.raw_query = raw_query
        result.technologies = [t for t in (data.get("technologies") or []) if t and t != "null"]

        for field, attr in [("date_from", "date_from"), ("date_to", "date_to")]:
            if data.get(field):
                try:
                    setattr(result, attr, datetime.fromisoformat(str(data[field])))
                except (ValueError, TypeError):
                    pass

        fmt = data.get("format")
        if fmt and fmt in ("online", "offline", "hybrid"):
            result.format = fmt

        for field in ("location", "theme", "prize", "other"):
            val = data.get(field)
            if val and val != "null":
                setattr(result, field, val)

        sl = data.get("skill_level")
        if sl and sl in ("beginner", "intermediate", "advanced"):
            result.skill_level = sl

        for field in ("team_size", "duration_hours"):
            val = data.get(field)
            if val and val != "null":
                try:
                    setattr(result, field, int(val))
                except (ValueError, TypeError):
                    pass

        return result

    def generate_embedding(self, text: str) -> List[float]:
        try:
            return self.embedding_model.encode(text).tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}", exc_info=True)
            return []

    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        if not embedding1 or not embedding2:
            return 0.0
        arr1, arr2 = np.array(embedding1), np.array(embedding2)
        return float(np.dot(arr1, arr2) / (np.linalg.norm(arr1) * np.linalg.norm(arr2) + 1e-10))

    def rank_hackathons(
        self, query: str, hackathons: List[Dict], limit: int = 10, exclude_ids: List[int] = None
    ) -> Tuple[List[Dict], Dict, List[str]]:
        if exclude_ids is None:
            exclude_ids = []

        parsed = self.parse_user_query(query)
        query_embedding = self.generate_embedding(query)

        scored = []
        for h in hackathons:
            if h.get("id") in exclude_ids:
                continue
            score = self._score_hackathon(h, parsed, query_embedding)
            if score > 0:
                scored.append({"score": score, "hackathon": h})

        scored.sort(key=lambda x: x["score"], reverse=True)
        results = [item["hackathon"] for item in scored[:limit]]

        for h in results:
            self.recommended_hackathons.add(h.get("id"))

        follow_up = self.generate_follow_up_questions(parsed)
        return results, parsed.to_dict(), follow_up

    def _score_hackathon(self, hackathon: Dict, parsed: ParsedQuery, query_embedding: List[float]) -> float:
        h_text = f"{hackathon.get('title', '')} {hackathon.get('description', '')}"
        techs = hackathon.get("technologies", [])
        if techs:
            h_text += f" {' '.join(techs)}"
        if hackathon.get("theme"):
            h_text += f" {hackathon['theme']}"

        semantic = self.calculate_similarity(query_embedding, self.generate_embedding(h_text))
        bonus, penalty = 0.0, 0.0

        # Date filter
        if parsed.date_from or parsed.date_to:
            start, end = hackathon.get("start_date"), hackathon.get("end_date")
            if start and end:
                for val in (start, end):
                    if isinstance(val, str):
                        try:
                            val = datetime.fromisoformat(val)
                        except (ValueError, TypeError):
                            val = None
                if start and end:
                    match = True
                    if parsed.date_from and end < parsed.date_from:
                        match = False
                    if parsed.date_to and start > parsed.date_to:
                        match = False
                    bonus += 0.2 if match else 0
                    penalty += 0 if match else 0.3

        if parsed.format:
            h_fmt = hackathon.get("format", "").lower()
            if h_fmt == parsed.format:
                bonus += 0.15
            elif h_fmt and h_fmt != parsed.format and parsed.format != "hybrid":
                penalty += 0.15

        if parsed.location:
            h_loc = (hackathon.get("location") or "").lower()
            if parsed.location.lower() in h_loc or h_loc in parsed.location.lower():
                bonus += 0.15
            elif h_loc:
                penalty += 0.1

        if parsed.technologies:
            h_techs = [t.lower() for t in hackathon.get("technologies", [])]
            matched = sum(1 for t in parsed.technologies if t.lower() in h_techs)
            bonus += 0.2 * (matched / len(parsed.technologies))

        if parsed.skill_level:
            h_level = (hackathon.get("skill_level") or "any").lower()
            if h_level == parsed.skill_level or h_level == "any":
                bonus += 0.1
            else:
                penalty += 0.05

        if parsed.theme:
            h_theme = (hackathon.get("theme") or "").lower()
            if parsed.theme.lower() in h_theme or h_theme in parsed.theme.lower():
                bonus += 0.15

        if parsed.team_size:
            t_min, t_max = hackathon.get("team_size_min"), hackathon.get("team_size_max")
            if t_min is not None and t_max is not None and t_min <= parsed.team_size <= t_max:
                bonus += 0.05

        if parsed.duration_hours:
            h_dur = hackathon.get("duration_hours")
            if h_dur and abs(h_dur - parsed.duration_hours) / max(parsed.duration_hours, 1) <= 0.2:
                bonus += 0.05

        if parsed.prize:
            h_prize = (hackathon.get("prize") or "").lower()
            if parsed.prize.lower() in h_prize:
                bonus += 0.05

        return max((semantic * 0.4) + bonus - penalty, 0.0)

    def generate_follow_up_questions(self, parsed: ParsedQuery) -> List[str]:
        missing = parsed.get_missing_fields()
        if not missing:
            return []

        field_desc = {
            "technologies": "технологии или языки программирования",
            "dates": "период или даты проведения",
            "format": "формат участия (онлайн/офлайн/гибрид)",
            "location": "город или страна проведения",
            "skill_level": "уровень подготовки участников",
            "theme": "тематика хакатона",
            "team_size": "размер команды",
            "prize": "призы или награды",
            "duration_hours": "длительность хакатона",
        }
        missing_desc = [field_desc[f] for f in missing if f in field_desc]

        prompt = f"""Ты — помощник по поиску хакатонов. Пользователь ищет хакатон, но не указал некоторые детали.

Запрос пользователя: "{parsed.raw_query}"
Неуказанные параметры: {', '.join(missing_desc)}

Сгенерируй ровно 3-4 коротких наводящих вопроса на русском языке для уточнения самых важных параметров.
Каждый вопрос на отдельной строке, без нумерации. ТОЛЬКО вопросы."""

        try:
            response = self.ollama_client.generate(model=self.model_name, prompt=prompt, stream=False)
            raw = response.get("response", "").strip()
            questions = [q.strip().lstrip("0123456789.)-–•► ") for q in raw.split("\n") if q.strip()]
            return [q for q in questions if len(q) > 10][:4]
        except Exception as e:
            logger.error(f"Error generating follow-up questions: {e}", exc_info=True)
            fallback = {
                "technologies": "Какие технологии или языки программирования вас интересуют?",
                "dates": "В какой период вы хотели бы участвовать?",
                "format": "Вам удобнее онлайн или офлайн формат?",
                "location": "В каком городе вы ищете хакатон?",
                "skill_level": "Какой у вас уровень подготовки?",
                "theme": "Какая тематика вас интересует?",
                "team_size": "Сколько человек планируете в команде?",
                "prize": "Важны ли для вас призы?",
                "duration_hours": "Какая длительность хакатона предпочтительна?",
            }
            return [fallback[f] for f in missing if f in fallback][:4]

    def reset_recommendations(self):
        self.recommended_hackathons.clear()

    def get_recommended_hackathon_ids(self) -> List[int]:
        return list(self.recommended_hackathons)
