# Corpus and Ingestion Requirements

A robust Retrieval-Augmented Generation (RAG) system depends on a clean, coherent document corpus, deterministic text preprocessing, and an efficient vector indexing pipeline.

---

## 1. Document Corpus Specification

- **Scope & Volume**: Assemble a coherent corpus of company policies and procedures comprising **5 to 20 documents** totaling **30 to 120 pages** (or equivalent word count).
- **Supported File Formats**: Support standard multi-format files such as Markdown (`.md`), Plain Text (`.txt`), HTML (`.html`), and/or PDF (`.pdf`).
- **Domain Topics**: The corpus must cover realistic organizational policy categories, including:
  - Paid Time Off (PTO), Sick Leave, and Parental Leave
  - Information Security, Data Handling, and Acceptable Device Use
  - Travel, Meals, and Expense Reimbursement
  - Remote Work, Hybrid Schedule, and Home Office Policies
  - Observed Company Holidays, Working Hours, and Overtime
  - Employee Conduct, Grievance Procedures, and Anti-Harassment
- **Data Governance & Legal Compliance**:
  - Documents must be legal to include in the public repository or dynamically load at runtime.
  - Use synthetic policies (authored with AI assistance) or publicly shareable corporate policies.
  - **No private, proprietary, or paid confidential data** should be used.

---

## 2. Environment and Reproducibility

- **Virtual Environment**: Use an isolated environment (`venv`, `conda`, or `poetry`).
- **Dependency Management**: Clearly pin all required packages in `requirements.txt` (or `environment.yml` / `pyproject.toml`).
- **Deterministic Processing & Fixed Seeds**:
  - Set fixed random seeds (e.g., `seed = 42`) where applicable for deterministic chunking, embedding generation, or evaluation set sampling.
- **Documentation**: Provide a root `README.md` with explicit, copy-pasteable setup and execution commands.

---

## 3. Parsing, Cleaning, and Preprocessing

- **Document Ingestion**: Implement loaders capable of reading files from the corpus directory.
- **Text Cleaning**: Strip superfluous HTML tags, abnormal whitespace, non-printable characters, headers, footers, or formatting artifacts that could pollute embeddings.
- **Metadata Tagging**: Attach essential metadata to each document/chunk:
  - `doc_id`: Unique document identifier
  - `title`: Human-readable document name
  - `section` / `heading`: Relevant heading or subtopic
  - `source`: File path or canonical reference

---

## 4. Chunking Strategy

- **Chunking Method**: Implement a deliberate chunking strategy:
  - *Heading-based / Semantic Chunking*: Splitting logically by sections/markdown headers, or
  - *Token / Character Windows with Overlap*: Sliding window (e.g., 500–1000 characters or 256–512 tokens with 10–20% overlap).
- **Boundary Preservation**: Avoid splitting sentences or key policy clauses arbitrarily across chunk boundaries.

---

## 5. Embeddings and Vector Indexing

- **Cloud Embedding Model**: Utilize OpenRouter's free-tier cloud embedder:
  - **Primary Model**: `nvidia/llama-nemotron-embed-vl-1b-v2:free` via OpenRouter Embeddings API (`https://openrouter.ai/api/v1/embeddings`).
  - **Benefits**: Completely offloads embedding compute to the cloud, eliminating local deep learning dependencies and ensuring ultra-fast cold starts and minimal memory consumption on Render.
  - **Fallback/Testing**: Support automated offline/mock embedding for CI/CD test runs when API keys are not supplied.
- **Vector Database**: Store chunk embeddings in a persistent local ChromaDB instance (`data/chroma_db/`).
- **Persistent Storage**: Ensure vector indexes persist across server restarts so documents do not need to be re-embedded on every application launch.
