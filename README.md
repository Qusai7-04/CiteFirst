# CiteFirst — Research Assistant with Citations

CiteFirst is a citation-grounded research assistant for querying scientific paper collections. It pairs hybrid document retrieval and cross-encoder reranking with a multi-stage corrective triage pipeline, anchoring generated answers to inspected PDF passages with verified source filenames and physical page numbers.

An answer, retrieval score, citation, or status badge is never an automated guarantee of factual truth: on development questions, generated answers achieved a 2/22 (9.1%) human acceptance rate, and all cited sources and physical page numbers require independent human verification against the original papers.

---

## Architecture Overview

```mermaid
flowchart TD
    User([User Query]) --> UI[Next.js 16 Web UI<br/>app/ components/ hooks/]
    UI -->|HTTP / SSE Stream| API[FastAPI Local Bridge<br/>api.py :8000]
    API --> Engine[CiteFirst Logic Engine<br/>logic_engine.py]

    subgraph Retrieval["Stage 1: Hybrid Retrieval (database.py)"]
        Chroma[(ChromaDB<br/>bge-small-en-v1.5<br/>Dense Vectors)]
        BM25[(BM25 Cache<br/>Sparse Lexical)]
        RRF[Reciprocal Rank Fusion<br/>k=60, FETCH_K=30]
        Chroma --> RRF
        BM25 --> RRF
    end

    Engine --> Retrieval
    Retrieval -->|Top 30 Candidates| Rerank["Stage 2: Cross-Encoder Reranking<br/>BAAI/bge-reranker-base (PROCESS_K=10)"]
    Rerank --> Grade{"Stage 3: Tri-State Grading<br/>Sigmoid Thresholds"}
    
    Grade -->|Correct >= 0.55| Verified[Verified Passages]
    Grade -->|Ambiguous 0.25 - 0.55| Resolve["Stage 4: Ambiguous Resolution<br/>Sentence Extraction & Supplemental Search"]
    Grade -->|Incorrect < 0.25| Discard[Discarded Passages]
    Resolve --> Verified

    Verified --> PreFlight{"Stage 5: Pre-Flight Check<br/>Combined Context Verification"}
    PreFlight -->|Pass| LLM["Stage 6: Adaptive Generation (providers.py)<br/>OpenRouter: meta-llama/llama-3.3-70b-instruct"]
    PreFlight -->|Fail / Empty| Fallback[Query Rewrite & Fallback Routing]
    Fallback --> LLM

    LLM --> Stream([SSE Stream to UI<br/>Status, Answer & Cited Page Badges])
```

---

## The Six Pipeline Stages

CiteFirst implements corrective retrieval-augmented generation across six modular stages:

1. **Stage 1 — Hybrid Retrieval (Dense + BM25 + RRF)**:
   - **Dense vector search**: `BAAI/bge-small-en-v1.5` embeddings (384 dimensions) stored locally in ChromaDB.
   - **Sparse lexical search**: BM25 corpus matching with query tokenization and in-memory caching.
   - **Reciprocal Rank Fusion (RRF)**: Merges dense and sparse rankings to collect an initial candidate pool of 30 chunks (`FETCH_K=30`).
   - **Parent-Child Expansion**: Chunks are scored at focused sentence level (100 words), while enclosing parent chunks (350 words) provide paragraph context for the generator.
2. **Stage 2 — Cross-Encoder Reranking**:
   - `BAAI/bge-reranker-base` cross-encoder evaluates joint query-passage cross-attention.
   - Predictions are batched for high-throughput CPU inference. Top 10 passages (`PROCESS_K=10`) are normalized via sigmoid scaling.
3. **Stage 3 — Tri-State Grading**:
   - Candidate chunks are categorized into three confidence tiers:
     - **Correct** (score ≥ 0.55): Directly accepted into verified evidence context.
     - **Ambiguous** (0.25 ≤ score < 0.55): Forwarded to ambiguous resolution.
     - **Incorrect** (score < 0.25): Discarded as irrelevant noise.
4. **Stage 4 — Ambiguous Resolution**:
   - Extracts the highest-scoring sentence from ambiguous chunks and runs targeted supplemental searches to rescue or discard candidate passages.
5. **Stage 5 — Pre-Flight Combined Relevance Verification**:
   - Evaluates whether the combined set of verified passages sufficiently answers the user query before invoking generation, mitigating hallucination and false positives.
6. **Stage 6 — Adaptive Citation-Grounded Generation**:
   - Passes verified evidence to OpenRouter LLMs (`meta-llama/llama-3.3-70b-instruct` by default).
   - Generates responses anchored to the provided context with structured citations (source PDF filename, 1-based physical PDF page number, and evidence snippets).

---

## Quickstart

### Prerequisites

- **Python**: 3.10 to 3.14 (tested on Python 3.14)
- **Node.js**: 18+ (tested on Node.js 22)
- **OpenRouter API Key**: Obtain a key at [openrouter.ai](https://openrouter.ai)

### 1. Backend Setup

```bash
# Clone the private repository
git clone https://github.com/Qusai7-04/CiteFirst.git
cd CiteFirst

# Create and activate a Python virtual environment
python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
# source .venv/bin/activate

# Install backend dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt

# Configure environment variables
cp .env.example .env
```

Edit `.env` and set your OpenRouter API key:
```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

Start the backend API server:
```bash
python -m uvicorn api:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Frontend Setup

In a separate terminal window:
```bash
# Install Node dependencies
npm install

# Start the Next.js development server
npm run dev
```

Open `http://127.0.0.1:3000` in your web browser.

---

## Document Ingestion & Vault

CiteFirst operates on local PDF papers:

1. **Web Interface**: Upload PDF papers directly via the `/vault` page or within `/chat`. PyMuPDF extracts text page-by-page, chunks into child/parent segments, and indexes embeddings into `./vector_vault/`.
2. **Batch Upload**: Place PDFs in the `papers/` folder and run:
   ```bash
   python database.py
   ```
3. **Data Privacy**: All PDF text, embeddings, and SQLite metadata remain strictly local on your machine and are excluded from Git.

---

## Evaluation Benchmark & Verified Results

CiteFirst was evaluated against its local benchmark corpus of **66 academic research papers** (7,816 chunks).

### 1. Chunk-Level Relevance Evaluation

Evaluated using an LLM Grader (`meta-llama/llama-3.1-8b-instruct`) on the 66-paper corpus across **593 chunk-level relevance classifications**:

- **Accuracy**: **0.9848**
- **Precision**: **0.7000**
- **Recall**: **0.8235**
- **F1 Score**: **0.7568**

#### Confusion Matrix (593 Chunk Decisions)

| | Predicted Irrelevant | Predicted Relevant | Total Decisions |
| :--- | :---: | :---: | :---: |
| **Actual Irrelevant** | **570** (True Negatives) | **6** (False Positives) | 576 |
| **Actual Relevant** | **3** (False Negatives) | **14** (True Positives) | 17 |
| **Total Predictions** | 573 | 20 | **593** |

> [!IMPORTANT]
> **Understanding Chunk Relevance vs. Answer Correctness**:
> The high accuracy (98.48%) is driven primarily by the large true-negative denominator (570 correct rejections of irrelevant passages out of 593 total decisions; 570 + 6 + 3 + 14 = 593). This measures the chunk filter's ability to reject distractor passages. **It does NOT represent the accuracy of generated answers.**

### 2. Answer-Accuracy Evaluation (Human Review)

Answer correctness was evaluated across **26 human-reviewed questions** with signed evidence sign-offs and structured verdict forms, partitioned into 22 development questions and a disclosed 4-question pilot:

| Partition | Questions | ACCEPT | PARTIAL | REJECT | Claim Coverage (Covered / Partial / Omitted) | Approved Pages in Context |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Development (Q001–Q022)** | 22 | **2 (9.1%)** | **9 (40.9%)** | **11 (50.0%)** | 14 / 21 / 39 (N=74) | 15 / 22 |
| **Disclosed Pilot (Q023–Q026)** | 4 | **4 (100.0%)** | **0 (0.0%)** | **0 (0.0%)** | 9 / 0 / 0 (N=9) | 4 / 4 |
| **Overall Benchmark Total** | **26** | **6 (23.1%)** | **9 (34.6%)** | **11 (42.3%)** | **23 / 21 / 39 (N=83)** | **19 / 26** |

#### Key Evaluation Findings
- **Context Presence vs. Claim Synthesis**: In 19 of 26 questions (73.1%), approved source pages successfully reached the generation context. However, multi-part synthesis requirements caused the generator to miss secondary claims or output cautious abstentions.
- **Pilot Generalizability Caveat**: The pilot questions (Q023–Q026) were inspected during prompt tuning; their 4/4 acceptance rate is disclosed as an internal pilot and must not be interpreted as an unbiased general holdout rate.

### 3. Historical Ablation Study

The table below reflects the progressive ablation findings from the initial research study by Sushant Shekhar Sinha, Kanan Gupta, and Qusai:

| Configuration | Accuracy | Precision | Recall | F1 Score | Notes |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Dense-only baseline** (no logic) | 0.938 | 0.390 | 0.760 | 0.514 | High noise, low precision |
| **Hybrid dense + BM25 / RRF** | 0.885 | 0.380 | 0.860 | 0.525 | Higher recall, broader pool |
| **Hybrid + Cross-Encoder** (static thresholds) | 0.910 | 0.480 | 0.720 | 0.576 | Reranker sharpens top ranks |
| **Full Logic + Chunk-level verification** | 0.974 | 0.500 | 0.670 | 0.572 | Early gate reduced true positives |
| **Full Logic + Pre-flight combined check** | **0.985** | **0.700** | **0.820** | **0.760** | Final architecture; cuts false positives |

*(Note: Baseline ablations conducted during early exploratory development are not directly comparable to later frozen-protocol evaluations.)*

For detailed protocols, cryptographic manifests, and signed verdict sheets, see the [Pipeline Evaluation & Benchmark Report](docs/evaluation/evaluation_report.md) and [`docs/evaluation/phase4_questions.json`](docs/evaluation/phase4_questions.json).

---

## Development & Test Commands

```bash
# Run full backend test suite (offline / mock-enabled)
python -m pytest tests/

# Compile Python source
python -m compileall -q api.py database.py logic_engine.py providers.py settings_config.py

# Frontend linting
npm run lint

# Frontend TypeScript type check
npx tsc --noEmit

# Production Next.js build
npm run build
```

---

## Operational Scope & Security

- **Local Desktop Workstation Target**: CiteFirst binds strictly to `127.0.0.1:8000` and `127.0.0.1:3000`.
- **Single-User Architecture**: The FastAPI service does not implement multi-user authentication or multi-tenant database isolation. It should not be exposed to public networks without an authenticating reverse proxy.
- **Corpus & Reproduction Boundaries**: Under copyright and storage hygiene, source PDF papers and vector store files are not checked into Git. Ingest your own PDFs to initialize the local vector vault.

---

## Lineage & Attribution

- **Lineage**: CiteFirst evolved from a university research project on Corrective RAG at Manipal Institute of Technology developed by **Sushant Shekhar Sinha**, **Kanan Gupta**, and **Qusai**. See [`NOTICE.md`](NOTICE.md) for full historical contributor attribution.
- **Licensing**: CiteFirst intentionally does not include a root project `LICENSE` file. All rights are reserved by the authors, with upstream libraries and model weights governed by their respective licenses (ChromaDB, PyMuPDF, SentenceTransformers, Hugging Face).
