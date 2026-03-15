import os
from typing import List, Dict, Set
from sentence_transformers import SentenceTransformer
import numpy as np
from dotenv import load_dotenv
import ollama
from backend.config.logging_config import get_logger

load_dotenv()

logger = get_logger(__name__)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


class AIRecommender:
    def __init__(self):
        """Initialize the AI recommender with Qwen2 and embeddings model"""
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.ollama_client = ollama.Client(host=OLLAMA_BASE_URL)
        self.model_name = "qwen2"  # Qwen2 model for text generation
        self.recommended_hackathons: Set[int] = set()  # Track recommended hackathons per session

    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a given text"""
        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating embedding: {e}", exc_info=True)
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
        self, query: str, hackathons: List[Dict], limit: int = 10, exclude_ids: List[int] = None
    ) -> List[Dict]:
        """Rank hackathons by relevance to user query, filtering out already recommended ones"""
        if exclude_ids is None:
            exclude_ids = []

        query_embedding = self.generate_embedding(query)

        scored_hackathons = []
        for hackathon in hackathons:
            # Skip already recommended hackathons
            if hackathon.get("id") in exclude_ids:
                continue

            # Build hackathon text with title, description, and technologies
            hackathon_text = f"{hackathon.get('title', '')} {hackathon.get('description', '')}"

            # Include technology tags in the text for better semantic matching
            technologies = hackathon.get("technologies", [])
            if technologies:
                hackathon_text += f" {' '.join(technologies)}"

            hackathon_embedding = self.generate_embedding(hackathon_text)
            similarity = self.calculate_similarity(query_embedding, hackathon_embedding)

            scored_hackathons.append({"score": similarity, "hackathon": hackathon})

        sorted_hackathons = sorted(scored_hackathons, key=lambda x: x["score"], reverse=True)
        results = [item["hackathon"] for item in sorted_hackathons[:limit]]

        # Update the set of recommended hackathons
        for h in results:
            self.recommended_hackathons.add(h.get("id"))

        return results

    def reset_recommendations(self):
        """Reset the set of recommended hackathons"""
        self.recommended_hackathons.clear()

    def generate_hackathon_suggestion(self, query: str, technologies: List[str] = None) -> str:
        """Use Qwen2 to generate helpful suggestions for hackathon search"""
        try:
            tech_context = ""
            if technologies:
                tech_context = f"\nAvailable technologies: {', '.join(technologies)}"

            prompt = f"""Based on the user's interest in '{query}', suggest relevant hackathon categories or skills they might be interested in. Keep response brief (1-2 sentences).{tech_context}"""

            response = self.ollama_client.generate(
                model=self.model_name,
                prompt=prompt,
                stream=False,
            )

            return response.get("response", "").strip()
        except Exception as e:
            logger.error(f"Error generating suggestion with Qwen2: {e}", exc_info=True)
            return ""

    def extract_hackathon_features(self, description: str) -> Dict:
        """Use Qwen2 to extract key features/skills from hackathon description"""
        try:
            prompt = f"""Extract the main programming languages, technologies, and skills relevant to this hackathon. Format as comma-separated values:

Description: {description}

Response:"""

            response = self.ollama_client.generate(
                model=self.model_name,
                prompt=prompt,
                stream=False,
            )

            return {"features": response.get("response", "").strip()}
        except Exception as e:
            logger.error(f"Error extracting features: {e}", exc_info=True)
            return {"features": ""}

    def get_recommended_hackathon_ids(self) -> List[int]:
        """Get list of already recommended hackathon IDs"""
        return list(self.recommended_hackathons)

