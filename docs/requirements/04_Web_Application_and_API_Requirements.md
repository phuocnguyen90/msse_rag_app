# Web Application and API Requirements

The project requires an accessible, user-friendly interface and a standard REST API allowing users and external services to interact with the RAG pipeline.

---

## 1. Technology Options

- **Web Frameworks**: You may choose:
  - **Flask / FastAPI**: Recommended for creating explicit REST endpoints with a dedicated frontend template or lightweight single-page interface.
  - **Streamlit**: Acceptable for rapid UI prototyping, provided all three required routes (`/`, `/chat`, `/health`) are properly exposed or integrated.
- **Orchestration**: LangChain, LlamaIndex, or lightweight custom Python services.

---

## 2. Required Endpoints and Interface

### A. Web Chat Interface (`GET /`)
- An interactive web page featuring:
  - A clean, modern chat interface or query submission box.
  - Display area for conversation history or question-and-answer pairs.
  - Visually distinct rendering of citations and expandable source snippet previews.
  - Visual indicators for system state (loading/generating indicator, error alerts).

### B. Chat API Endpoint (`POST /chat`)
- Accepts a JSON payload containing the user query:
  ```json
  {
    "question": "What is the maximum reimbursement for business meals?"
  }
  ```
- Returns a structured JSON response containing the generated answer, citations, and retrieved passage snippets:
  ```json
  {
    "answer": "Employees may be reimbursed up to $75 per day for business meals with itemized receipts [Expense-Policy, Section 4.2].",
    "citations": [
      {
        "doc_id": "EXP-2025",
        "title": "Corporate Travel & Expense Policy",
        "section": "Section 4.2 - Meals and Incidental Expenses",
        "snippet": "The daily meal reimbursement allowance is capped at $75 per diem. Itemized receipts are mandatory for all claims exceeding $25."
      }
    ]
  }
 Pared/source links should allow users to verify the exact policy snippet backing each claim.

### C. Health Check Endpoint (`GET /health`)
- Returns a lightweight JSON status check for uptime monitoring and CI/CD smoke tests:
  ```json
  {
    "status": "ok",
    "version": "1.0.0",
    "vector_store": "ready"
  }
  ```
- HTTP status code `200 OK` when healthy.

---

## 3. Error Handling and User Experience

- **Input Validation**: Gracefully handle empty queries, excessively long prompts, or malformed JSON payloads with appropriate HTTP status codes (`400 Bad Request`).
- **Resilience**: Return informative error messages if external LLM APIs experience rate limits, timeouts, or network failures (`503 Service Unavailable` or friendly UI message).
- **Security Best Practices**:
  - Securely inject API keys via environment variables (never hardcoded in source files or frontend scripts).
  - Sanitize user inputs and escape rendered HTML to avoid Cross-Site Scripting (XSS).
