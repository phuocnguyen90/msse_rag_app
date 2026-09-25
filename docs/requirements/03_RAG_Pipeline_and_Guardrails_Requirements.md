# RAG Pipeline and Guardrails Requirements

The Retrieval-Augmented Generation (RAG) pipeline is responsible for finding relevant document excerpts based on user queries, synthesizing grounded answers, and enforcing strict response constraints.

---

## 1. Retrieval Strategy

- **Top-$k$ Retrieval**: Implement semantic similarity retrieval parameterized by $k$ (e.g., $k \in [3, 5]$). The retriever must return the top-$k$ most relevant text chunks from the vector database based on cosine similarity or inner product distance.
- **Optional Re-ranking**: You may optionally implement cross-encoder re-ranking (e.g., FlashRank, Cohere Re-ranker, or a HuggingFace cross-encoder) to re-order the retrieved candidates before passing them to the generation prompt.
- **Metadata Passthrough**: Ensure that along with the chunk text, all associated metadata (`doc_id`, `title`, `section`, `source_url`/`path`) is forwarded to the generator and client.

---

## 2. Prompting and Context Injection Strategy

- **Prompt Construction**: Design a structured system prompt that clearly delineates:
  1. **Role Definition**: Act as the company's internal HR and policy assistant.
  2. **Context Block**: Clearly delimit the retrieved context snippets (e.g., using XML tags `<context>...</context>` or Markdown fences).
  3. **Metadata Association**: Clearly indicate the `[Doc ID: X, Title: Y]` for each excerpt in the context so the model can cite accurately.
  4. **Grounding Directive**: Require the model to formulate answers exclusively based on the provided context. If the answer cannot be determined from the context, the model must trigger a guardrail refusal.
- **LLM Integration**:
  - Connect to a cost-effective or zero-cost LLM provider (e.g., Groq using `llama-3.3-70b-versatile` / `llama-3.1-8b-instant`, OpenRouter free models, or user-provided OpenAI/Anthropic keys).
  - Configure hyperparameters (e.g., temperature $\le 0.2$ for deterministic, factual responses).

---

## 3. Mandatory Guardrails

The application must enforce three core guardrails:

1. **Out-of-Corpus Refusal (Domain Bounding)**:
   - When a user asks a question not addressed in the policy corpus (e.g., general world knowledge, coding questions, competitive intelligence, or unstated policies), the model **must refuse to answer**.
   - Standard refusal phrasing: *"I can only answer questions regarding our company policies and procedures based on the provided documentation."*
   - Explicit prohibition against hallucinating or extrapolating unwritten policies.

2. **Strict Citation and Attribution**:
   - Every substantive claim in an answer **must explicitly cite** the source document ID or document title (e.g., `[PTO-Policy-2025, Section 3.1]`).
   - Citations must accurately point to the specific passage supporting the claim.

3. **Output Length Control**:
   - Limit the generation length (e.g., `max_tokens` set to 300–500 tokens) to ensure answers remain concise, actionable, and focused on relevant policy clauses without rambling.

---

## 4. Pipeline Orchestration

- You may use frameworks such as **LangChain**, **LlamaIndex**, or build a custom Python orchestration pipeline using native API calls.
- Modularize the retrieval logic, prompt formatting, model invocation, and citation extraction so components can be tested and benchmarked independently.
