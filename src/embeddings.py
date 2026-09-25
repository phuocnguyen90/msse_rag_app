"""OpenRouter Cloud Embeddings Module.

Integrates with OpenRouter's OpenAI-compatible /embeddings endpoint,
specifically utilizing nvidia/llama-nemotron-embed-vl-1b-v2:free.
Includes graceful fallback for offline unit tests and CI/CD environments.
"""

import hashlib
import logging
import math
import os
from typing import List, Optional
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from openai import OpenAI

logger = logging.getLogger(__name__)

DEFAULT_EMBEDDING_MODEL = "nvidia/llama-nemotron-embed-vl-1b-v2:free"
DEFAULT_DIMENSION = 2048


def _generate_mock_embedding(text: str, dim: int = DEFAULT_DIMENSION) -> List[float]:
    """Generate a deterministic Bag-of-Words feature hashing vector.

    Used when OPENROUTER_API_KEY is not configured or in offline test mode.
    Maps words to hash buckets with sign hashing so term overlaps produce
    positive cosine similarity for accurate offline retrieval.
    """
    import re
    vec = [0.0] * dim
    words = re.findall(r"\w+", text.lower())
    if not words:
        return vec

    for word in words:
        h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        sign = 1.0 if (h >> 32) % 2 == 0 else -1.0
        vec[idx] += sign

    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


class OpenRouterEmbeddingFunction(EmbeddingFunction[Documents]):
    """ChromaDB compatible EmbeddingFunction that queries OpenRouter."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        base_url: str = "https://openrouter.ai/api/v1",
        batch_size: int = 16,
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = model_name or os.getenv(
            "OPENROUTER_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL
        )
        self.base_url = base_url
        self.batch_size = batch_size

        if self.api_key:
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                timeout=15.0,
            )
        else:
            self.client = None
            logger.warning(
                "OPENROUTER_API_KEY is not set. Operating in offline mock embedding mode."
            )

    @staticmethod
    def name() -> str:
        return "openrouter_embedding_function"

    def get_config(self) -> dict:
        return {"model_name": self.model_name}

    @staticmethod
    def build_from_config(config: dict) -> "OpenRouterEmbeddingFunction":
        return OpenRouterEmbeddingFunction(model_name=config.get("model_name"))

    def __call__(self, input: Documents) -> Embeddings:
        """Embed a list of documents for ChromaDB."""
        if not input:
            return []

        if not self.client:
            return [_generate_mock_embedding(doc) for doc in input]

        all_embeddings: List[List[float]] = []
        try:
            for i in range(0, len(input), self.batch_size):
                batch = input[i:i + self.batch_size]
                response = self.client.embeddings.create(
                    model=self.model_name,
                    input=batch,
                )
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            return all_embeddings
        except Exception as e:
            logger.error(
                f"Error calling OpenRouter embeddings API ({self.model_name}): {e}. "
                "Falling back to deterministic offline embeddings."
            )
            return [_generate_mock_embedding(doc) for doc in input]
