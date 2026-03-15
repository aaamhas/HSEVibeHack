import os
import json
import re
from typing import List, Dict, Set, Optional
from datetime import datetime, timedelta
from sentence_transformers import SentenceTransformer
import numpy as np
from dotenv import load_dotenv
import ollama

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


class ParsedQuery:
    """Structured representation of parsed user query"""

    def __init__(self):
        self.technologies: List[str] = []
        self.date_from: Optional[datetime] = None
        self.date_to: Optional[datetime] = None
        self.format: Optional[str] = None  # online, offline, hybrid
        self.location: Optional[str] = None
        self.skill_level: Optional[str] = None  # beginner, intermediate, advanced
        self.theme: Optional[str] = None  # fintech, ai, gamedev, etc.
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
        """Return list of field names that are not filled"""
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
        """Initialize the AI recommender with Qwen2 and embeddings model"""
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.ollama_client = ollama.Client(host=OLLAMA_BASE_URL)
        self.model_name = "qwen2"
        self.recommended_hackathons: Set[int] = set()

    def parse_user_query(self, query: str) -> ParsedQuery:
        """Use Qwen2 to extract structured data from user's natural language query"""
        today = datetime.utcnow()

        prompt = f"""You are a JSON extraction assistant. Extract structured information from the user's hackathon search query.
Today's date: {today.strftime('%Y-%m-%d')}

User query: "{query}"

Extract the following fields. Return ONLY valid JSON, no extra text:
{{
    "technologies": ["list of programming languages, frameworks, tools mentioned"],
    "date_from": "YYYY-MM-DD or null (start of desired period)",
    "date_to": "YYYY-MM-DD or null (end of desired period)",
    "format": "online/offline/hybrid or null",
    "location": "city or country or null",
    "skill_level": "beginner/intermediate/advanced or null",
    "theme": "hackathon theme like fintech, ai, gamedev, healthcare, education, cybersecurity, social, sustainability, web3 or null",
    "team_size": number or null (preferred team size),
    "prize": "money/internship/job/certificates or null (what kind of prize user wants)",
    "duration_hours": number or null (preferred duration in hours, e.g. 24, 48, 168 for a week),
    "other": "any other important details from the query that don't fit above categories, or null"
}}

Rules:
- For relative dates: "spring" = March 1 to May 31, "summer" = June 1 to August 31, "autumn/fall" = September 1 to November 30, "winter" = December 1 to February 28
- "next week" = next Monday to Sunday, "next month" = first to last day of next month
- "weekend hackathon" → duration_hours: 48
- "24-hour hackathon" → duration_hours: 24
- If user mentions "beginner-friendly" or "for beginners" → skill_level: "beginner"
- Only extract what is explicitly mentioned or clearly implied
- Return null for fields not mentioned
- Return ONLY the JSON object"""

        try:
            response = self.ollama_client.generate(
                model=self.model_name,
                prompt=prompt,
                stream=False,
            )

            raw_response = response.get("response", "").strip()
            parsed = self._extract_json(raw_response)
            return self._build_parsed_query(parsed, query, today)

        except Exception as e:
            print(f"Error parsing query with Qwen2: {e}")
            # Fallback: return query as-is with no structured data
            result = ParsedQuery()
            result.raw_query = query
            return result

    def _extract_json(self, text: str) -> Dict:
        """Extract JSON from LLM response, handling markdown code blocks"""
        # Try to find JSON in code blocks
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if json_match:
            text = json_match.group(1).strip()

        # Try to find JSON object directly
        json_match = re.search(r"\{[\s\S]*\}", text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        return {}

    def _build_parsed_query(self, data: Dict, raw_query: str, today: datetime) -> ParsedQuery:
        """Build ParsedQuery from extracted JSON data"""
        result = ParsedQuery()
        result.raw_query = raw_query

        result.technologies = data.get("technologies") or []
        # Clean out null/None values from technologies list
        result.technologies = [t for t in result.technologies if t and t != "null"]

        if data.get("date_from"):
            try:
                result.date_from = datetime.fromisoformat(str(data["date_from"]))
            except (ValueError, TypeError):
                pass

        if data.get("date_to"):
            try:
                result.date_to = datetime.fromisoformat(str(data["date_to"]))
            except (ValueError, TypeError):
                pass

        fmt = data.get("format")
        if fmt and fmt in ("online", "offline", "hybrid"):
            result.format = fmt

        result.location = data.get("location") if data.get("location") != "null" else None
        result.theme = data.get("theme") if data.get("theme") != "null" else None
        result.prize = data.get("prize") if data.get("prize") != "null" else None
        result.other = data.get("other") if data.get("other") != "null" else None

        sl = data.get("skill_level")
        if sl and sl in ("beginner", "intermediate", "advanced"):
            result.skill_level = sl

        if data.get("team_size") and data["team_size"] != "null":
            try:
                result.team_size = int(data["team_size"])
            except (ValueError, TypeError):
                pass

        if data.get("duration_hours") and data["duration_hours"] != "null":
            try:
                result.duration_hours = int(data["duration_hours"])
            except (ValueError, TypeError):
                pass

        return result

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a given text"""
        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return []

    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings"""
        if not embedding1 or not embedding2:
            return 0.0

        arr1 = np.array(embedding1)
        arr2 = np.array(embedding2)
        similarity = np.dot(arr1, arr2) / (np.linalg.norm(arr1) * np.linalg.norm(arr2) + 1e-10)
        return float(similarity)

    def rank_hackathons(
        self,
        query: str,
        hackathons: List[Dict],
        limit: int = 10,
        exclude_ids: List[int] = None,
    ) -> List[Dict]:
        """Rank hackathons using structured parsing + semantic similarity"""
        if exclude_ids is None:
            exclude_ids = []

        parsed = self.parse_user_query(query)
        query_embedding = self.generate_embedding(query)

        scored_hackathons = []
        for hackathon in hackathons:
            if hackathon.get("id") in exclude_ids:
                continue

            score = self._score_hackathon(hackathon, parsed, query_embedding)
            if score > 0:
                scored_hackathons.append({"score": score, "hackathon": hackathon})

        sorted_hackathons = sorted(scored_hackathons, key=lambda x: x["score"], reverse=True)
        results = [item["hackathon"] for item in sorted_hackathons[:limit]]

        for h in results:
            self.recommended_hackathons.add(h.get("id"))

        follow_up_questions = self.generate_follow_up_questions(parsed)

        return results, parsed.to_dict(), follow_up_questions

    def _score_hackathon(
        self, hackathon: Dict, parsed: ParsedQuery, query_embedding: List[float]
    ) -> float:
        """Calculate composite score for a hackathon based on structured filters + semantic similarity"""

        # --- Semantic similarity (base score, weight 0.4) ---
        hackathon_text = f"{hackathon.get('title', '')} {hackathon.get('description', '')}"
        technologies = hackathon.get("technologies", [])
        if technologies:
            hackathon_text += f" {' '.join(technologies)}"
        theme = hackathon.get("theme")
        if theme:
            hackathon_text += f" {theme}"

        hackathon_embedding = self.generate_embedding(hackathon_text)
        semantic_score = self.calculate_similarity(query_embedding, hackathon_embedding)

        # --- Structured matching (bonus scores) ---
        bonus = 0.0
        penalty = 0.0

        # Date filter (weight 0.2)
        if parsed.date_from or parsed.date_to:
            start = hackathon.get("start_date")
            end = hackathon.get("end_date")
            if start and end:
                if isinstance(start, str):
                    try:
                        start = datetime.fromisoformat(start)
                    except (ValueError, TypeError):
                        start = None
                if isinstance(end, str):
                    try:
                        end = datetime.fromisoformat(end)
                    except (ValueError, TypeError):
                        end = None

                if start and end:
                    date_match = True
                    if parsed.date_from and end < parsed.date_from:
                        date_match = False
                    if parsed.date_to and start > parsed.date_to:
                        date_match = False

                    if date_match:
                        bonus += 0.2
                    else:
                        penalty += 0.3  # Strong penalty for wrong dates

        # Format filter (weight 0.15)
        if parsed.format:
            h_format = hackathon.get("format", "").lower()
            if h_format == parsed.format:
                bonus += 0.15
            elif h_format and h_format != parsed.format and parsed.format != "hybrid":
                penalty += 0.15

        # Location filter (weight 0.15)
        if parsed.location:
            h_location = (hackathon.get("location") or "").lower()
            if parsed.location.lower() in h_location or h_location in parsed.location.lower():
                bonus += 0.15
            elif h_location:
                penalty += 0.1

        # Technology match (weight 0.2)
        if parsed.technologies:
            h_techs = [t.lower() for t in hackathon.get("technologies", [])]
            matched = sum(1 for t in parsed.technologies if t.lower() in h_techs)
            if parsed.technologies:
                tech_ratio = matched / len(parsed.technologies)
                bonus += 0.2 * tech_ratio

        # Skill level (weight 0.1)
        if parsed.skill_level:
            h_level = (hackathon.get("skill_level") or "any").lower()
            if h_level == parsed.skill_level or h_level == "any":
                bonus += 0.1
            else:
                penalty += 0.05

        # Theme match (weight 0.15)
        if parsed.theme:
            h_theme = (hackathon.get("theme") or "").lower()
            if parsed.theme.lower() in h_theme or h_theme in parsed.theme.lower():
                bonus += 0.15

        # Team size (weight 0.05)
        if parsed.team_size:
            t_min = hackathon.get("team_size_min")
            t_max = hackathon.get("team_size_max")
            if t_min is not None and t_max is not None:
                if t_min <= parsed.team_size <= t_max:
                    bonus += 0.05

        # Duration (weight 0.05)
        if parsed.duration_hours:
            h_duration = hackathon.get("duration_hours")
            if h_duration:
                # Allow 20% tolerance
                if abs(h_duration - parsed.duration_hours) / max(parsed.duration_hours, 1) <= 0.2:
                    bonus += 0.05

        # Prize (weight 0.05)
        if parsed.prize:
            h_prize = (hackathon.get("prize") or "").lower()
            if parsed.prize.lower() in h_prize:
                bonus += 0.05

        final_score = (semantic_score * 0.4) + bonus - penalty
        return max(final_score, 0.0)

    def generate_follow_up_questions(self, parsed: ParsedQuery) -> List[str]:
        """Generate 3-4 follow-up questions based on missing fields in parsed query"""
        missing = parsed.get_missing_fields()
        if not missing:
            return []

        field_descriptions = {
            "technologies": "технологии или языки программирования",
            "dates": "период или даты проведения",
            "format": "формат участия (онлайн/офлайн/гибрид)",
            "location": "город или страна проведения",
            "skill_level": "уровень подготовки участников",
            "theme": "тематика или направление хакатона",
            "team_size": "размер команды",
            "prize": "призы или награды",
            "duration_hours": "длительность хакатона",
        }

        missing_descriptions = [field_descriptions[f] for f in missing if f in field_descriptions]

        prompt = f"""Ты — помощник по поиску хакатонов. Пользователь ищет хакатон, но не указал некоторые важные детали.

Запрос пользователя: "{parsed.raw_query}"

Неуказанные параметры: {', '.join(missing_descriptions)}

Сгенерируй ровно 3-4 коротких наводящих вопроса на русском языке, чтобы уточнить самые важные из неуказанных параметров. Вопросы должны быть дружелюбными и естественными.

Правила:
- Выбери 3-4 самых важных параметра из неуказанных (не спрашивай про все)
- Каждый вопрос на отдельной строке
- Без нумерации и маркеров
- Формат ответа — ТОЛЬКО вопросы, каждый на новой строке, без лишнего текста"""

        try:
            response = self.ollama_client.generate(
                model=self.model_name,
                prompt=prompt,
                stream=False,
            )

            raw = response.get("response", "").strip()
            questions = [q.strip().lstrip("0123456789.)-–•► ") for q in raw.split("\n") if q.strip()]
            # Filter out empty or too short lines
            questions = [q for q in questions if len(q) > 10]
            return questions[:4]

        except Exception as e:
            print(f"Error generating follow-up questions: {e}")
            return self._fallback_questions(missing)

    def _fallback_questions(self, missing: List[str]) -> List[str]:
        """Generate static fallback questions if Qwen2 is unavailable"""
        fallback_map = {
            "technologies": "Какие технологии или языки программирования вас интересуют?",
            "dates": "В какой период вы хотели бы участвовать в хакатоне?",
            "format": "Вам удобнее онлайн или офлайн формат?",
            "location": "В каком городе или стране вы ищете хакатон?",
            "skill_level": "Какой у вас уровень подготовки — начинающий, средний или продвинутый?",
            "theme": "Какая тематика хакатона вас интересует (AI, fintech, gamedev и т.д.)?",
            "team_size": "Сколько человек вы планируете в команде?",
            "prize": "Важны ли для вас призы (деньги, стажировки, сертификаты)?",
            "duration_hours": "Какая длительность хакатона для вас предпочтительна?",
        }
        questions = [fallback_map[f] for f in missing if f in fallback_map]
        return questions[:4]

    def reset_recommendations(self):
        """Reset the set of recommended hackathons"""
        self.recommended_hackathons.clear()

    def get_recommended_hackathon_ids(self) -> List[int]:
        """Get list of already recommended hackathon IDs"""
        return list(self.recommended_hackathons)
