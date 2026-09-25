# Design and Evaluation Document

## Executive Summary
This document provides the architectural justifications, design decisions, and empirical evaluation results for the **Apex Technologies Policy Assistant**—a production-grade Retrieval-Augmented Generation (RAG) web application and REST API designed to answer employee policy inquiries with verifiable citations, strict factual grounding, and domain-bounded guardrails.

Rather than evaluating exclusively on "happy-path" questions, the benchmark suite explicitly stress-tests the system against **borderline cases, multi-policy conflicts, exact numerical boundary conditions, and disguised corporate inquiries** to identify where and why the model stumbles when resolving complex real-world context.

---

## 1. Design & Architectural Decisions

### 1.1 Embedding Model Choice
- **Model Selected**: `nvidia/llama-nemotron-embed-vl-1b-v2:free` via OpenRouter Embeddings API (with deterministic signed Bag-of-Words feature hashing as zero-dependency offline fallback).
- **Rationale**:
  - Eliminates heavy local deep learning dependencies (e.g., PyTorch ~2.5GB CUDA wheels), drastically reducing cold start times and container slug size.
  - Minimal memory footprint (< 150MB), preventing Out-Of-Memory (OOM) crashes on Render's 512MB RAM free tier.
  - High semantic fidelity with 2048-dimensional dense vectors specifically optimized for technical and corporate text retrieval.

### 1.2 Chunking Strategy
- **Methodology**: Hierarchical Section-Aware Chunking with Sliding Window Overlap.
- **Parameters**: Maximum chunk length of 700 characters (~150 tokens) with a 120-character overlap (~25 tokens).
- **Rationale**:
  - Preserves organizational policy context by splitting primarily along Markdown section headings (`##` and `###`).
  - Prepends document ID and section title metadata (`[POL-EXP-2025: Section 4.2]`) directly into each chunk's embedding representation.
  - Overlap prevents sentence boundary shearing and ensures multi-clause regulations remain contiguous.

### 1.3 Vector Store Selection
- **Technology**: **ChromaDB** (Persistent Local Mode).
- **Distance Metric**: Cosine Similarity (`hnsw:space: "cosine"`).
- **Rationale**:
  - Embedded, serverless operation with zero network overhead for vector querying.
  - Fully persists indexed vectors to disk (`data/chroma_db/`), allowing the application to start immediately without re-embedding the corpus on every web server reboot.
  - Native integration with custom embedding functions and metadata filtering.

### 1.4 Generation Model Architecture & Rate Control
- **Primary Model**: `nex-agi/nex-n2.5-mini:free` (fast, deterministic instruction-following with sub-second generation).
- **Dynamic Failover**: `google/gemma-4-26b-a4b-it:free`, `nvidia/nemotron-3.5-lightning:free`, and `liquid/lfm-2.5-2.6b:free`.
- **Reasoning Control & Token Guard**:
  - Configures `extra_body={"reasoning": {"exclude": True}}` on OpenRouter to suppress unformatted chain-of-thought scratchpads from leaking into completion streams.
  - Dedicated sanitization parser `_clean_llm_response()` strips lingering thinking tags and recovers the core answer even if an upstream model emits internal reasoning steps.
- **Rate-Throttling**: Evaluation runner implements a 1.5s politeness delay between queries with 10.0s client timeout and single retry to prevent 429 rate limit errors on OpenRouter's free tier.

### 1.5 Mandatory Defensive Guardrails
1. **Out-of-Corpus Refusal**: Non-policy queries (general knowledge, coding, sports, weather) trigger the canonical refusal:
   > *"I can only answer questions regarding our company policies and procedures based on the provided documentation."*
2. **Mandatory Citations**: Every substantive statement requires inline citations formatted as `[Doc ID, Section]`.
3. **Length Limiter**: Generation ceiling capped at 250 words / 800 max tokens to ensure concise, executive-level summaries.

---

## 2. Evaluation Approach & Empirical Benchmark Results

### 2.1 Benchmark Dataset (25 Stress-Test Inquiries)
The evaluation benchmark (`eval/benchmark_data.json`) spans 10 corporate policy domains across 5 rigorous test categories:
1. **Standard Factual (10 items)**: Direct, single-clause policy lookups (baseline happy path).
2. **Borderline Tension / Multi-Policy Conflict (5 items)**: Inter-document policy conflicts requiring the model to resolve overriding exceptions (e.g. Travel Meal Cap $75 vs. Client Dinner Cap $150; Remote Equipment Stipend $500 vs. Banned NAS Storage).
3. **Borderline Boundary Conditions (4 items)**: Strict numerical inequalities ($25.00 vs $25.01 receipt requirement, $50.00 vs $50.01 gift surrender rule, 40-hour rollover cap, 90-min vs 2-hour outage).
4. **Borderline Disguised / Unspecified Scenarios (3 items)**: Inquiries disguised as plausible corporate policy that require subtle category discrimination (e.g. ADA service animals vs emotional support pets; lunch-hour crypto trading bots; campus drone flights).
5. **Adversarial Refusal (3 items)**: Clear out-of-scope non-policy requests (sports scores, coding scripts, historical trivia).

### 2.2 Evaluation Metrics & Empirical Results

| Metric | Target Standard | Achieved Score | Evaluation Status |
| :--- | :---: | :---: | :---: |
| **Overall Groundedness** | $\ge 75\%$ | **80.0%** | Exceeds Target |
| **Overall Citation Accuracy** | $\ge 85\%$ | **96.0%** | Exceeds Target |
| **Median Latency ($p_{50}$)** | $< 4000\text{ ms}$ | **3077.7 ms** | Fast & Production-Grade |
| **Tail Latency ($p_{95}$)** | $< 8000\text{ ms}$ | **5811.1 ms** | High Reliability |
| **Mean Latency** | $< 4500\text{ ms}$ | **3383.5 ms** | Stable & Predictable |
| **Adversarial Refusal Adherence** | $100\%$ | **100.0%** | Zero Hallucinations |

### 2.3 Category Performance Breakdown

| Evaluation Category | Test Items | Groundedness % | Citation Acc % | Failure Count | Primary Challenge |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Factual Standard** | 10 | 80.0% | 100.0% | 2 | Single-clause factual retrieval |
| **Borderline Tension** | 5 | 80.0% | 80.0% | 1 | Multi-document exception override |
| **Borderline Boundary** | 4 | **50.0%** | 100.0% | 2 | Exact arithmetic & strict inequality bounds |
| **Borderline Disguised** | 3 | 100.0% | 100.0% | 0 | Nuanced category discrimination (ESAs vs ADA) |
| **Adversarial Refusal** | 3 | 100.0% | 100.0% | 0 | Strict refusal boundary enforcement |

---

## 3. Failure Mode Analysis: Stress-Testing the RAG Pipeline

By intentionally engineering adversarial and borderline queries, the evaluation suite uncovered three distinct failure modes inherent to real-world corporate RAG deployments:

### Failure Mode 1: Context Distractor & Semantic Misdirection (Q10)
- **Question**: *"Within how many days must an employee report an ethics or conduct grievance?"*
- **Expected Document**: `POL-WBL-2025` (Whistleblower and Grievance Procedure Policy, Section 2: 30 days).
- **Observed Behavior**: The retriever pulled `POL-COC-2025` (Code of Conduct) because the query contained "conduct grievance". The Code of Conduct states that harassment should be reported "immediately", leading the model to state: *"The policy does not specify a fixed number of days for reporting an ethics or conduct grievance; harassment should be reported immediately. [POL-COC-2025, Sec 2]"*.
- **Root Cause**: Dense vector embeddings can suffer from lexical attraction toward overlapping policy titles.
- **Architectural Mitigation**: Implemented hybrid sparse-dense re-ranking and metadata filtering by document domain tags.

### Failure Mode 2: Over-Conservative Guardrail Refusal in Exception Scenarios (Q15)
- **Question**: *"Can an employee on an emergency customer support rotation take summer Friday afternoons off at 1:00 PM?"*
- **Expected Resolution**: The model should cite `POL-HOL-2025`, explaining that while general staff log off at 1:00 PM, critical support staff must maintain coverage and take compensatory time off on an alternate weekday.
- **Observed Behavior**: The model triggered the standard refusal response: *"I can only answer questions regarding our company policies and procedures based on the provided documentation."*
- **Root Cause**: When the model detects tension between a general permission (Summer Fridays) and an operational constraint (support rotation), high defensive guardrail prompts can trigger a false-positive refusal rather than synthesizing the compensatory time compromise.
- **Architectural Mitigation**: Refined the prompt instructions to distinguish between unmentioned topics (refuse) versus complex conditional permissions (explain constraints).

### Failure Mode 3: Boundary Condition Lexical Sensitivity (Q17, Q19)
- **Question**: *"I took a taxi from the airport that cost exactly $25.00 USD. Do I need an itemized merchant receipt to expense it?"*
- **Observed Answer**: *"No. Since the charge was exactly $25.00, an itemized merchant receipt is not required; a simple credit card receipt or bank statement proof is accepted. [POL-EXP-2025, Sec 5]"*
- **Analysis**: The model **correctly deduced the strict boundary inequality** ($25.00 exact is exempt; $25.01 requires itemization). However, automated string comparison penalized the answer due to lexical variation compared to the gold answer phrasing.
- **Takeaway**: Strict numerical boundaries require semantic evaluation or LLM-as-a-judge scoring rather than rigid token overlap heuristics.

---

## 4. Retrieval Depth ($k$) Ablation Study

We measured vector retrieval latency and multi-document coverage across varying retrieval depths:

| Retrieval Depth ($k$) | Average Retrieval Time | Relevant Passage Coverage | Cross-Policy Synthesis Success | Prompt Token Overhead |
| :---: | :---: | :---: | :---: | :---: |
| **$k = 2$** | 833.2 ms | 88.0% | Poor (missed secondary policy chunks) | Minimal (~350 tokens) |
| **$k = 4$** | **821.4 ms** | **98.0%** | **Optimal (successfully bridges multi-doc conflicts)** | **Moderate (~700 tokens)** |
| **$k = 6$** | 903.3 ms | 100.0% | Marginal gain over $k=4$ | High (~1100 tokens, higher latency) |

**Empirical Conclusion**: Top-$k = 4$ provides the optimal trade-off between prompt token efficiency, sub-second retrieval latency, and the multi-document coverage necessary to resolve cross-policy borderline cases.
