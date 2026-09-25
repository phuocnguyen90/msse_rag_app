"""Ingestion and Indexing Pipeline.

Loads corporate policy documents, chunks them with section metadata and overlap,
generates embeddings, and stores them in a persistent ChromaDB vector index.
"""

import argparse
import glob
import logging
import os
import re
import sys
from typing import Any, Dict, List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from src.embeddings import OpenRouterEmbeddingFunction  # noqa: E402

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_CORPUS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "corpus")
DEFAULT_DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "chroma_db")
COLLECTION_NAME = "policy_corpus"


def parse_document_metadata(content: str, filename: str) -> Dict[str, str]:
    """Extract metadata such as title and doc_id from document content."""
    lines = content.strip().split("\n")
    title = os.path.splitext(os.path.basename(filename))[0].replace("_", " ").title()
    doc_id = os.path.splitext(os.path.basename(filename))[0].upper()

    for line in lines:
        if line.startswith("# ") and not title:
            title = line.replace("# ", "").strip()
        elif line.startswith("# "):
            title = line.replace("# ", "").strip()

        id_match = re.search(r"\*\*Document ID:\*\*\s*([A-Za-z0-9_-]+)", line)
        if id_match:
            doc_id = id_match.group(1).strip()

    return {"title": title, "doc_id": doc_id, "source": os.path.basename(filename)}


def chunk_document_by_sections(
    content: str,
    metadata: Dict[str, str],
    max_chunk_chars: int = 700,
    overlap_chars: int = 120,
) -> List[Dict[str, Any]]:
    """Chunk a markdown policy document preserving section headings and content coherence."""
    lines = content.split("\n")
    chunks = []
    current_section = "General Overview"
    current_lines: List[str] = []

    def flush_chunk(lines_to_flush: List[str], section_name: str) -> None:
        text = "\n".join(lines_to_flush).strip()
        if not text:
            return
        if len(text) <= max_chunk_chars:
            chunks.append({
                "text": text,
                "metadata": {
                    "doc_id": metadata["doc_id"],
                    "title": metadata["title"],
                    "section": section_name,
                    "source": metadata["source"],
                },
            })
        else:
            # Sub-split into overlapping windows
            start = 0
            while start < len(text):
                end = min(start + max_chunk_chars, len(text))
                sub_text = text[start:end].strip()
                if sub_text:
                    chunks.append({
                        "text": sub_text,
                        "metadata": {
                            "doc_id": metadata["doc_id"],
                            "title": metadata["title"],
                            "section": section_name,
                            "source": metadata["source"],
                        },
                    })
                if end == len(text):
                    break
                start = end - overlap_chars

    for line in lines:
        # Check for markdown heading (## or ###)
        if line.startswith("## ") or line.startswith("### "):
            if current_lines:
                flush_chunk(current_lines, current_section)
                current_lines = []
            current_section = line.lstrip("#").strip()
            current_lines.append(line)
        else:
            current_lines.append(line)

    if current_lines:
        flush_chunk(current_lines, current_section)

    return chunks


def build_vector_index(
    corpus_dir: str = DEFAULT_CORPUS_DIR,
    db_dir: str = DEFAULT_DB_DIR,
    reset: bool = False,
) -> int:
    """Index all documents in corpus_dir into ChromaDB."""
    logger.info(f"Indexing policy corpus from: {corpus_dir}")
    logger.info(f"Target ChromaDB directory: {db_dir}")

    os.makedirs(db_dir, exist_ok=True)
    os.makedirs(corpus_dir, exist_ok=True)

    client = chromadb.PersistentClient(path=db_dir)
    embedding_fn = OpenRouterEmbeddingFunction()

    if reset:
        try:
            client.delete_collection(name=COLLECTION_NAME)
            logger.info(f"Deleted existing collection: {COLLECTION_NAME}")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn,
        metadata={"hnsw:space": "cosine"},
    )

    doc_files = sorted(
        glob.glob(os.path.join(corpus_dir, "*.md"))
        + glob.glob(os.path.join(corpus_dir, "*.txt"))
        + glob.glob(os.path.join(corpus_dir, "*.html"))
    )

    if not doc_files:
        logger.warning(f"No document files found in {corpus_dir}!")
        return 0

    total_chunks = 0
    all_ids = []
    all_texts = []
    all_metadatas = []

    for file_path in doc_files:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        meta = parse_document_metadata(content, file_path)
        chunks = chunk_document_by_sections(content, meta)

        for idx, chunk in enumerate(chunks):
            chunk_id = f"{meta['doc_id']}_chunk_{idx:03d}"
            all_ids.append(chunk_id)
            # Prepend context to help semantic search
            enriched_text = f"[{meta['doc_id']}: {meta['title']} - {chunk['metadata']['section']}]\n{chunk['text']}"
            all_texts.append(enriched_text)
            chunk["metadata"]["chunk_index"] = idx
            all_metadatas.append(chunk["metadata"])

    if all_ids:
        # Chroma upsert in batches of 50
        batch_size = 50
        for i in range(0, len(all_ids), batch_size):
            collection.upsert(
                ids=all_ids[i:i + batch_size],
                documents=all_texts[i:i + batch_size],
                metadatas=all_metadatas[i:i + batch_size],
            )
        total_chunks = len(all_ids)

    logger.info(
        f"Indexing complete! Ingested {len(doc_files)} policy documents "
        f"into {total_chunks} searchable vector chunks."
    )
    return total_chunks


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest policy corpus into ChromaDB.")
    parser.add_argument("--corpus-dir", default=DEFAULT_CORPUS_DIR, help="Path to corpus files")
    parser.add_argument("--db-dir", default=DEFAULT_DB_DIR, help="Path to ChromaDB directory")
    parser.add_argument("--reset", action="store_true", help="Reset existing vector collection")
    args = parser.parse_args()

    build_vector_index(corpus_dir=args.corpus_dir, db_dir=args.db_dir, reset=args.reset)
