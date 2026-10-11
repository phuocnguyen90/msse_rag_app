# Live Application Deployment Information

## Deployed Application URL
- **Live URL**: [https://msse-rag-app.onrender.com/](https://msse-rag-app.onrender.com/) *(Configured via `render.yaml`)*
- **Health Check Endpoint**: [https://msse-rag-app.onrender.com/health](https://msse-rag-app.onrender.com/health)
- **Chat REST API**: [https://msse-rag-app.onrender.com/chat](https://msse-rag-app.onrender.com/chat)

### Diagnostic & Sub-Component Endpoints
To verify each pipeline component in isolation on the cloud container:
- **Cloud Embeddings**: [https://msse-rag-app.onrender.com/api/diag-embed](https://msse-rag-app.onrender.com/api/diag-embed) *(OpenRouter cloud embedder)*
- **Cloud LLM Generation**: [https://msse-rag-app.onrender.com/api/diag-llm](https://msse-rag-app.onrender.com/api/diag-llm) *(Meta Llama 3.1 8B Instruct)*
- **Vector Retrieval**: [https://msse-rag-app.onrender.com/api/diag-retrieve](https://msse-rag-app.onrender.com/api/diag-retrieve) *(In-memory vector ranker + ChromaDB)*

---

## Deployment Platform & Configuration
- **Platform**: Render.com (Web Service, Free Tier, Oregon)
- **Hardware Profile**: 0.1–0.5 fractional vCPU (cgroups shared CPU), 512 MB RAM
- **Infrastructure as Code**: `render.yaml`
- **Runtime**: Python 3.12.9
- **Server**: Gunicorn (`--workers 1 --threads 4 --timeout 60`)
- **Primary Chat Model**: `meta-llama/llama-3.1-8b-instruct` (Fast, high groundedness, ~2–3s)
- **Fallback Chat Model**: `openai/gpt-oss-20b` (Automated failover candidate)
- **Embedding Provider**: OpenRouter Cloud Embedder (`nvidia/llama-nemotron-embed-vl-1b-v2:free`, 2048 dimensions)
- **Vector Database**: ChromaDB (`data/chroma_db/`, 77 pre-indexed chunks) + In-Memory Vector Cosine Ranker
- **Single-Core Concurrency Control**: `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`, `MKL_NUM_THREADS=1` to prevent cgroup thread deadlocks
- **Circuit Breaker**: Module-level `ThreadPoolExecutor` with 12s timeout shield and safe offline fallback

---

## Verification & Smoke Test
You can verify the deployment status and vector health at any time:

### 1. Health Check via `curl`:
```bash
curl -X GET https://msse-rag-app.onrender.com/health
```

**Live Verified Response**:
```json
{
  "api_key_configured": true,
  "chat_model": "meta-llama/llama-3.1-8b-instruct",
  "indexed_chunks": 77,
  "service": "apex-policy-rag-assistant",
  "status": "healthy",
  "vector_store": "ready",
  "version": "1.0.0"
}
```

### 2. Isolated Diagnostics via `curl`:
```bash
# Verify OpenRouter embeddings API in isolation (~1.1s):
curl https://msse-rag-app.onrender.com/api/diag-embed

# Verify Meta Llama 3.1 8B Instruct chat generation in isolation (~0.9s):
curl https://msse-rag-app.onrender.com/api/diag-llm

# Verify vector retrieval in isolation (~0.9s):
curl https://msse-rag-app.onrender.com/api/diag-retrieve
```

### 3. End-to-End Chat Query via `curl`:
```bash
curl -i -X POST https://msse-rag-app.onrender.com/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "How many days of paid time off do employees get?"}'
```

**Live Verified Response (HTTP 200 OK)**:
```json
{
  "status": "success",
  "question": "How many days of paid time off do employees get?",
  "answer": "According to Section 2 of the Paid Time Off (PTO) and Leave Policy [POL-PTO-2025, Sec 2], the number of PTO days varies based on an employee's tenure with the company. The accrual rates are as follows:\n\n- Tier 1 (0 to 2 Years of Service): 15 days (120 hours) per calendar year\n- Tier 2 (2 to 5 Years of Service): 20 days (160 hours) per calendar year\n- Tier 3 (5+ Years of Service): 25 days (200 hours) per calendar year\n\nAdditionally, all full-time employees receive eight (8) paid sick days (64 hours) per calendar year on January 1, which is separate from their PTO accrual.",
  "citations": [
    {
      "doc_id": "POL-PTO-2025",
      "section": "2. PTO Accrual and Tiers",
      "snippet": "Full-time employees accrue PTO on a semi-monthly basis across each calendar pay period according to their tenure.",
      "title": "Paid Time Off (PTO) and Leave Policy"
    }
  ],
  "latency_ms": 7974.5,
  "model": "meta-llama/llama-3.1-8b-instruct"
}
```

---

## Collaborator Notice
Per the assignment submission guidelines:
- **`quantic-grader`** has been invited as a collaborator to the private GitHub repository with read access.
