# Apex Technologies — Policy & Procedures RAG Assistant

[![CI/CD Pipeline](https://github.com/phuocnguyen90/msse/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/phuocnguyen90/msse)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3123/)
[![Framework Flask](https://img.shields.io/badge/framework-Flask-black.svg)](https://flask.palletsprojects.com/)
[![VectorDB ChromaDB](https://img.shields.io/badge/vector_db-ChromaDB-orange.svg)](https://www.trychroma.com/)
[![Hosting Render](https://img.shields.io/badge/deploy-Render-46E3B7.svg)](https://render.com)

A production-grade Retrieval-Augmented Generation (RAG) web application and REST API that answers employee questions across a curated corpus of corporate policies with verifiable citations, strict factual grounding, and automated defensive guardrails.

---

## Key Features

- **Grounded Semantic Retrieval**: Powered by OpenRouter's cloud embedder `nvidia/llama-nemotron-embed-vl-1b-v2:free` and local persistent ChromaDB, eliminating heavy local PyTorch dependencies and keeping memory footprint under 150MB.
- **Defensive Guardrails**:
  - Automatically identifies and refuses out-of-corpus queries with the standardized response: *"I can only answer questions regarding our company policies and procedures based on the provided documentation."*
  - Strict inline citation enforcement (`[Doc ID, Section]`).
  - Output length constraints (concise, professional responses under 250 words).
- **Interactive Web Interface & REST API**:
  - Modern, responsive chat UI featuring pre-loaded suggested policy questions, real-time typing indicators, and expandable source snippet preview modals.
  - Standardized JSON REST API endpoints (`/chat`, `/health`) for programmatic integrations and uptime monitoring.
- **Production CI/CD & Cloud Deployment**:
  - Infrastructure as Code via `render.yaml` with Gunicorn WSGI binding for zero-cost deployment on Render.
  - Automated GitHub Actions workflow running linting, index validation, and smoke tests on every push and pull request.
- **Empirical Evaluation Benchmark**:
  - 20-question benchmark dataset across 10 corporate policies reporting **Groundedness %**, **Citation Accuracy %**, and **$p_{50}$ / $p_{95}$ Latency**.

---

## Architecture Flow

```
[Raw Policy Corpus (MD/TXT)]
            │
            ▼ (src/ingest.py)
[Section-Aware Chunker + Overlap]
            │
            ▼
[OpenRouter Cloud Embedder (Nemotron-Embed 2048-d)]
            │
            ▼
[Persistent ChromaDB Index (data/chroma_db/)]
            ▲
            │ (Top-k Semantic Retrieval)
[User Query] ──► [Flask REST API (app/app.py)] ──► [Grounded Prompt Builder]
                                                           │
                                                           ▼
                                                [OpenRouter Cloud LLM]
                                                (Nemotron 3.5 Lightning)
                                                           │
                                                           ▼
                                                [Answer + Citations + Snippets]
```

---

## Directory Structure

```
project_5_llm_app/
├── data/
│   ├── corpus/                # 10 comprehensive policy documents (~50 pages)
│   └── chroma_db/              # Persistent ChromaDB vector storage
├── src/
│   ├── embeddings.py          # OpenRouter cloud embedder with offline fallback
│   ├── ingest.py              # Parsing, chunking, and vector indexing pipeline
│   └── rag.py                 # Retrieval, prompt engineering, guardrails, & LLM client
├── app/
│   ├── app.py                 # Flask app factory, /chat, and /health routes
│   ├── templates/             # Modern HTML chat template (index.html)
│   └── static/                # CSS stylesheet (style.css) and client JS (main.js)
├── eval/
│   ├── benchmark_data.json    # 20 benchmark test questions across all policies
│   ├── evaluate.py            # Automated evaluation runner for quality & system metrics
│   └── evaluation_results.json# Detailed empirical benchmark output
├── tests/                     # Comprehensive Pytest unit and integration tests
├── .github/workflows/
│   └── ci-cd.yml              # GitHub Actions CI/CD automation workflow
├── render.yaml                # Render Infrastructure-as-Code deployment specification
├── requirements.txt           # Production pinned dependencies (zero torch)
├── run.py                     # Root execution entry point
├── README.md                  # Comprehensive setup and user guide
├── design-and-evaluation.md   # Architectural decisions & evaluation report
├── ai-tooling.md              # Reflection on AI tools and workflows used
└── deployed.md                # Live deployment URL and verification guide
```

---

## Quickstart & Local Setup

### 1. Prerequisites
- Python 3.11 or 3.12
- An OpenRouter API Key (free tier available at [openrouter.ai](https://openrouter.ai/))

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/phuocnguyen90/msse.git
cd msse/project_5_llm_app

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install lightweight dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the project root:
```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_EMBEDDING_MODEL=nvidia/llama-nemotron-embed-vl-1b-v2:free
OPENROUTER_CHAT_MODEL=nvidia/nemotron-3.5-lightning:free
```

### 4. Ingest and Index Policy Documents
```bash
python src/ingest.py --reset
```
*Expected output*: `Indexing complete! Ingested 10 policy documents into 70 searchable vector chunks.`

### 5. Launch the Web Application
```bash
python run.py
```
Open your browser and navigate to: **`http://localhost:5000`**

---

## API Endpoints

### 1. Interactive Web Chat Interface
- **Route**: `GET /`
- Renders the web interface with quick questions and citation drawers.

### 2. Chat Query Endpoint
- **Route**: `POST /chat`
- **Request Body**:
  ```json
  {
    "question": "What is the maximum daily reimbursement for business meals?"
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "question": "What is the maximum daily reimbursement for business meals?",
    "answer": "The maximum daily meal reimbursement is $75.00 USD per day for employees on overnight business travel [POL-EXP-2025, 4. Meals and Per Diem Allowances].",
    "citations": [
      {
        "doc_id": "POL-EXP-2025",
        "title": "Corporate Travel, Meals, and Expense Reimbursement Policy",
        "section": "4. Meals and Per Diem Allowances",
        "snippet": "Employees are eligible for a maximum total meal reimbursement of $75.00 USD per day while on overnight business travel."
      }
    ],
    "latency_ms": 1420.5,
    "model": "nvidia/nemotron-3.5-lightning:free"
  }
  ```

### 3. Health Check Endpoint
- **Route**: `GET /health`
- **Response**:
  ```json
  {
    "status": "healthy",
    "service": "apex-policy-rag-assistant",
    "version": "1.0.0",
    "vector_store": "ready",
    "indexed_chunks": 70,
    "chat_model": "nvidia/nemotron-3.5-lightning:free"
  }
  ```

---

## Running Automated Tests

Run the complete Pytest suite covering ingestion, retrieval, guardrails, and API endpoints:
```bash
pytest -v tests/
```

To run the automated benchmark evaluation:
```bash
python eval/evaluate.py
```

---

## Cloud Deployment (Render)

This application is ready for free-tier deployment on [Render](https://render.com) using the root `render.yaml` specification.

1. Connect your GitHub repository to Render.
2. Select **New Blueprint Instance** and point to `render.yaml`.
3. Add your `OPENROUTER_API_KEY` under Environment Variables.
4. Render will automatically build dependencies, execute vector indexing, and launch the Gunicorn server on port `$PORT`.

For live URL details and verification commands, see [deployed.md](file:///home/phuoc/git/msse/project_5_llm_app/deployed.md).

---

## Academic Integrity & Collaborator Notice
Per the assignment requirements:
- The repository is shared with the GitHub evaluation account **`quantic-grader`**.
- Detailed design and evaluation documentation is located in [design-and-evaluation.md](file:///home/phuoc/git/msse/project_5_llm_app/design-and-evaluation.md).
- AI tool reflections and methodology are documented in [ai-tooling.md](file:///home/phuoc/git/msse/project_5_llm_app/ai-tooling.md).
