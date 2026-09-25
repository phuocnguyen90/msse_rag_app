# Live Application Deployment Information

## Deployed Application URL
- **Live URL**: `https://apex-policy-rag.onrender.com/` *(Configured via `render.yaml`)*
- **Health Check Endpoint**: `https://apex-policy-rag.onrender.com/health`
- **Chat REST API**: `https://apex-policy-rag.onrender.com/chat`

---

## Deployment Platform & Configuration
- **Platform**: Render.com (Web Service, Free Tier)
- **Infrastructure as Code**: `render.yaml`
- **Runtime**: Python 3.12.3
- **Server**: Gunicorn (2 Workers, 4 Threads, 120s Timeout)
- **Embedding Provider**: OpenRouter Cloud Embedder (`nvidia/llama-nemotron-embed-vl-1b-v2:free`)
- **Generation Model**: OpenRouter Cloud LLM (`nvidia/nemotron-3.5-lightning:free`)
- **Vector Database**: Persistent ChromaDB (`data/chroma_db/`)
- **Health Check Path**: `/health` (Monitored by Render uptime agent)

---

## Verification & Smoke Test
You can verify the deployment status and vector health at any time:

### Health Check via `curl`:
```bash
curl -X GET https://apex-policy-rag.onrender.com/health
```

**Expected Response**:
```json
{
  "chat_model": "nvidia/nemotron-3.5-lightning:free",
  "indexed_chunks": 70,
  "service": "apex-policy-rag-assistant",
  "status": "healthy",
  "vector_store": "ready",
  "version": "1.0.0"
}
```

### Chat Query via `curl`:
```bash
curl -X POST https://apex-policy-rag.onrender.com/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the maximum reimbursement for business meals?"}'
```

---

## Collaborator Notice
Per the assignment submission guidelines:
- **`quantic-grader`** has been invited as a collaborator to the private GitHub repository with read access.
