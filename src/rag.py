"""RAG Pipeline and Guardrails Module.

Orchestrates semantic retrieval from ChromaDB, constructs grounded prompts
with metadata citations, enforces policy-domain guardrails, and interfaces with OpenRouter.
"""

import logging
import os
import re
import sys
import time
from typing import Any, Dict, List, Optional

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from openai import OpenAI  # noqa: E402
from src.embeddings import OpenRouterEmbeddingFunction  # noqa: E402

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chroma_db")
COLLECTION_NAME = "policy_corpus"
DEFAULT_CHAT_MODEL = os.getenv("OPENROUTER_CHAT_MODEL", "nvidia/nemotron-3.5-lightning:free")
FALLBACK_CHAT_MODELS = [
    DEFAULT_CHAT_MODEL,
    "liquid/lfm-2.5-2.6b:free",
    "google/gemma-4-26b-a4b-it:free",
]
STANDARD_REFUSAL = (
    "I can only answer questions regarding our company policies and procedures "
    "based on the provided documentation."
)

SYSTEM_PROMPT = """You are the official Internal Policy Assistant for Apex Technologies.
Your sole responsibility is to answer employee inquiries accurately and exclusively using the policy excerpts.

STRICT OPERATING RULES:
1. DIRECT ANSWER: Output directly the final response. Do NOT output internal thinking or scratchpad reasoning.
2. GROUNDEDNESS: Answer ONLY using information stated in the <context> excerpts. Do NOT assume external knowledge.
3. OUT-OF-CORPUS REFUSAL: If the question asks about something not in the policies, you MUST respond EXACTLY with:
"{refusal_phrase}"
4. CITATIONS: Every factual statement MUST include an explicit citation [Doc ID, Section] (e.g. [POL-PTO-2025, Sec 4]).
5. LENGTH LIMIT: Be concise and professional. Limit your response to 2-4 sentences. Do not exceed 250 words.

<context>
{context_block}
</context>
""".strip()


class PolicyRAGPipeline:
    """End-to-End Retrieval-Augmented Generation pipeline with guardrails."""

    def __init__(
        self,
        db_dir: str = DEFAULT_DB_DIR,
        collection_name: str = COLLECTION_NAME,
        chat_model: str = DEFAULT_CHAT_MODEL,
        api_key: Optional[str] = None,
        top_k: int = 3,
    ):
        self.db_dir = db_dir
        self.collection_name = collection_name
        self.chat_model = chat_model
        self.top_k = top_k
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")

        # Chroma vector collection
        self.chroma_client = chromadb.PersistentClient(path=self.db_dir)
        self.embedding_fn = OpenRouterEmbeddingFunction(api_key=self.api_key)
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

        # OpenRouter client
        if self.api_key:
            self.llm_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.api_key,
                timeout=15.0,
            )
        else:
            self.llm_client = None
            logger.warning(
                "OPENROUTER_API_KEY not configured. PolicyRAGPipeline running in offline fallback mode."
            )

    def retrieve(self, query: str, k: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve top-k relevant document chunks with metadata and distances."""
        limit = k or self.top_k
        if self.collection.count() == 0:
            return []

        results = self.collection.query(
            query_texts=[query],
            n_results=min(limit, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        retrieved_items = []
        if results and results["documents"] and results["documents"][0]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if results["metadatas"] else [{}] * len(docs)
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)

            for doc_text, meta, dist in zip(docs, metas, distances):
                # Clean snippet for client display
                clean_text = doc_text.split("]\n", 1)[-1] if "]\n" in doc_text else doc_text
                retrieved_items.append({
                    "snippet": clean_text.strip(),
                    "doc_id": meta.get("doc_id", "UNKNOWN"),
                    "title": meta.get("title", "Company Policy"),
                    "section": meta.get("section", "General"),
                    "source": meta.get("source", ""),
                    "distance": float(dist),
                })
        return retrieved_items

    def _offline_fallback_generator(
        self, query: str, retrieved_chunks: List[Dict[str, Any]]
    ) -> str:
        """Deterministic rule-based generator for offline testing when no API key is available."""
        if not retrieved_chunks:
            return STANDARD_REFUSAL

        query_lower = query.lower()
        out_of_scope_keywords = [
            "weather", "sports", "python code", "president", "capital of",
            "stock price of apple", "recipe", "quantum physics", "joke", "tell me a story"
        ]
        if any(kw in query_lower for kw in out_of_scope_keywords):
            return STANDARD_REFUSAL

        # Simple semantic keyword overlap check with retrieved chunks
        best_chunk = retrieved_chunks[0]
        snippet_sentences = [s.strip() for s in best_chunk["snippet"].split("\n") if s.strip()]

        # Filter lines relevant to query words
        query_words = set(re.findall(r"\w{4,}", query_lower))
        relevant_sentences = []
        for s in snippet_sentences:
            if any(w in s.lower() for w in query_words) and not s.startswith("#"):
                relevant_sentences.append(s.lstrip("- *"))

        if not relevant_sentences:
            relevant_sentences = [
                s.lstrip("- *") for s in snippet_sentences if not s.startswith("#")
            ][:2]

        if not relevant_sentences:
            return STANDARD_REFUSAL

        summary = " ".join(relevant_sentences[:2])
        doc_id = best_chunk["doc_id"]
        section = best_chunk["section"]
        return f"{summary} [{doc_id}, {section}]"

    def query(self, question: str, k: Optional[int] = None) -> Dict[str, Any]:
        """Execute full RAG retrieval and generation cycle with timing metrics."""
        start_time = time.time()
        question = question.strip()

        if not question:
            return {
                "question": question,
                "answer": "Please provide a valid policy question.",
                "citations": [],
                "latency_ms": 0.0,
                "model": self.chat_model,
            }

        # 1. Retrieval
        retrieval_start = time.time()
        chunks = self.retrieve(question, k=k)
        retrieval_ms = (time.time() - retrieval_start) * 1000

        # Build context block
        context_parts = []
        for idx, c in enumerate(chunks, 1):
            context_parts.append(
                f"[Source {idx}] Doc ID: {c['doc_id']} | Title: {c['title']} | Section: {c['section']}\n"
                f"{c['snippet']}"
            )
        context_block = "\n\n".join(context_parts)

        # 2. Generation with OpenRouter or offline fallback
        gen_start = time.time()
        answer = None
        used_model = self.chat_model

        if self.llm_client and self.api_key:
            prompt = SYSTEM_PROMPT.format(
                refusal_phrase=STANDARD_REFUSAL,
                context_block=context_block,
            )
            candidates = [self.chat_model] + [m for m in FALLBACK_CHAT_MODELS if m != self.chat_model]
            for model_candidate in candidates:
                try:
                    response = self.llm_client.chat.completions.create(
                        model=model_candidate,
                        messages=[
                            {"role": "system", "content": prompt},
                            {"role": "user", "content": question},
                        ],
                        temperature=0.1,
                        max_tokens=600,
                    )
                    raw_content = response.choices[0].message.content.strip()
                    # Strip any lingering thinking traces if present
                    if "</think>" in raw_content:
                        raw_content = raw_content.split("</think>")[-1].strip()
                    answer = raw_content
                    used_model = model_candidate
                    break
                except Exception as e:
                    logger.warning(f"Candidate model {model_candidate} failed: {e}. Trying next...")

        if not answer:
            answer = self._offline_fallback_generator(question, chunks)
            used_model = "offline-rule-generator"

        generation_ms = (time.time() - gen_start) * 1000
        total_latency_ms = (time.time() - start_time) * 1000

        # Format citations
        citations = []
        # If refusal, do not provide citations
        if STANDARD_REFUSAL.lower() not in answer.lower():
            for c in chunks:
                citations.append({
                    "doc_id": c["doc_id"],
                    "title": c["title"],
                    "section": c["section"],
                    "snippet": c["snippet"][:250] + "..." if len(c["snippet"]) > 250 else c["snippet"],
                })

        return {
            "question": question,
            "answer": answer,
            "citations": citations,
            "latency_ms": round(total_latency_ms, 2),
            "retrieval_ms": round(retrieval_ms, 2),
            "generation_ms": round(generation_ms, 2),
            "model": used_model,
        }
