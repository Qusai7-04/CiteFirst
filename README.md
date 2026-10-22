# CiteFirst

CiteFirst is a citation-grounded research application for question-answering across scientific papers. It couples hybrid passage retrieval and cross-encoder reranking with a corrective triage pipeline, aiming to anchor generated answers to inspected document text with source PDF filenames and physical page numbers.

An answer, retrieval score, citation, or status badge is never an automated guarantee of factual truth or complete citation accuracy: on development questions, generated answers achieved a 2/22 (9.1%) human acceptance rate, and all cited sources and physical pages require independent human verification against the original papers.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Next.js Frontend                         │
│         (app/, components/, hooks/, lib/, types/)           │
│           Interactive Chat, Vault, Pipeline, & Analytics     │
├─────────────────────────────────────────────────────────────┤
│                   FastAPI REST Bridge                       │
│                        (api.py)                             │
│       Local-only endpoints bound to 127.0.0.1:8000         │
├─────────────────────────────────────────────────────────────┤
│               Python Corrective Pipeline                    │
│     database.py   ──►   logic_engine.py   ──►  providers.py │
│   (Hybrid Search)     (4-Stage CRAG Triage)   (LLM Bridge)  │
├─────────────────────────────────────────────────────────────┤
│                   Local Data Stores                         │
│       vector_vault/ (ChromaDB)   │   vault.db (SQLite)      │
└─────────────────────────────────────────────────────────────┘
```

---

## The Four Pipeline Stages

CiteFirst implements Corrective Retrieval-Augmented Generation (CRAG) through four deterministic, traceable stages:

1. **Stage 1 — Hybrid Retrieval (Dense + BM25 + RRF)**
   - **Dense vector search**: `BAAI/bge-small-en-v1.5` embeddings (384 dimensions) indexed in ChromaDB.
   - **Sparse lexical search**: BM25 corpus matching with query preprocessing.
   - **Reciprocal Rank Fusion (RRF)**: Fuses dense and sparse rankings to retrieve a candidate pool of `FETCH_K=30` chunks.
   - **Parent-Child Expansion**: Chunks are scored at sentence level (child chunks), while enclosing parent chunks (up to 350 words) are expanded to supply coherent paragraph context.

2. **Stage 2 — Cross-Encoder Reranking**
   - **Model**: `BAAI/bge-reranker-base` cross-encoder.
   - Scores full query-passage cross-attention over fetched candidates.
   - Top `PROCESS_K=10` passages are selected and converted to normalized probabilities via sigmoid scaling.

3. **Stage 3 — Tri-State Grading & Pre-Flight Triage**
   - Candidate chunks are categorized into three confidence tiers:
     - **Correct** (confidence ≥ 0.55): High-confidence supporting evidence.
     - **Ambiguous** (0.25 ≤ confidence < 0.55): Potentially relevant context evaluated via LLM triage.
     - **Incorrect** (confidence < 0.25): Discarded as irrelevant.
   - **Pre-Flight Relevance Check**: If verified passages fail to answer the query, a rewritten query is triggered against the vault.

4. **Stage 4 — Citation-Grounded Answer Generation**
   - Passes only verified and resolved passages to the generation LLM.
   - Synthesizes the answer with strict instructions to anchor claims in the provided text.
   - Emits structured metadata including source PDF filenames, 1-based physical PDF page numbers, passage snippets, and pipeline status (`success`, `fallback_success`, `partial_match`, or `failed`).

---

## Setup and Installation

### Prerequisites

- **Python**: Version 3.10 to 3.14 (tested on Python 3.14)
- **Node.js**: Version 18+ (tested on Node.js 20+)
- **OS**: Windows, macOS, or Linux

### 1. Environment & Dependencies

#### On Windows (PowerShell):

```powershell
# Clone and enter the repository
cd C:\PROJECTS\CiteFirst

# Create and activate Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install Python backend dependencies
pip install -r requirements.txt

# Install Next.js frontend dependencies
npm install

# Configure environment variables
Copy-Item .env.example .env
```

#### On Unix-like Systems (Linux / macOS):

```bash
# Create and activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python backend dependencies
pip install -r requirements.txt

# Install Next.js frontend dependencies
npm install

# Configure environment variables
cp .env.example .env
```

### 2. Provider Configuration

Edit `.env` to configure your OpenRouter API key and model:

```dotenv
# OpenRouter Configuration (Single Supported Provider)
OPENROUTER_API_KEY=your_actual_key_here
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

---

## Running the Application

### Start the Backend API (FastAPI)

```bash
python -m uvicorn api:app --host 127.0.0.1 --port 8000 --reload
```

### Start the Frontend Web UI (Next.js)

In a separate terminal:

```bash
npm run dev
```

Open your browser to `http://127.0.0.1:3000`.

---

## Document Ingestion & Vault Setup

CiteFirst operates on user-supplied PDF documents:

1. **Web Interface**: Navigate to `/vault` or `/chat` in the web application and upload PDF papers directly. The system extracts text page-by-page using PyMuPDF, chunks content, and generates embeddings locally.
2. **Batch Ingestion Script**: Place PDFs in the local `papers/` directory and execute:
   ```bash
   python upload_papers.py
   ```
   *(Note: Uploads require the backend API to be running on `127.0.0.1:8000`.)*
3. **Data Storage**:
   - Vector collections are stored locally in `./vector_vault/` (ChromaDB).
   - Document metadata and upload history are tracked in `vault.db` (SQLite).
   - Both databases are strictly local and ignored by Git.

---

## Running Tests and Validation

### Python Backend Test Suite

Run the 98-item pytest test suite (covers provider error handling, retry policies, deterministic logic, vault paths, and evaluation benchmarks):

```bash
python -m pytest tests/
```

### Frontend Typechecking, Linting, & Production Build

```bash
# TypeScript strict type checking
npx tsc --noEmit

# ESLint code quality audit
npm run lint

# Next.js production build verification
npm run build
```

---

## Evaluation Benchmark & Verified Results

CiteFirst includes a canonical 26-question evaluation benchmark (`docs/evaluation/phase4_questions.json`) with signed human evidence sign-offs and answer verdicts.

### Partitioned Results Summary

| Partition | Total Qs | ACCEPT | PARTIAL | REJECT | Claim Coverage (Covered / Partial / Omitted) | Approved Pages in Context |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Development (Q001–Q022)** | 22 | **2 (9.1%)** | **9 (40.9%)** | **11 (50.0%)** | 14 / 21 / 39 (N=74) | 15 / 22 |
| **Disclosed Pilot (Q023–Q026)** | 4 | **4 (100.0%)** | **0 (0.0%)** | **0 (0.0%)** | 9 / 0 / 0 (N=9) | 4 / 4 |
| **Combined Descriptive Total** | **26** | **6 (23.1%)** | **9 (34.6%)** | **11 (42.3%)** | **23 / 21 / 39 (N=83)** | **19 / 26** |

### Critical Observed Limitations

1. **Development vs. Pilot Performance**: On the 22 iterative development questions (Q001–Q022), only **2 of 22 (9.1%)** generated answers received an `ACCEPT` verdict from human evaluation, with 9 receiving `PARTIAL` and 11 `REJECT`. Conversely, all 4 questions in the disclosed pilot partition (Q023–Q026) received `ACCEPT`. As documented in the [Evaluation Report](docs/evaluation/evaluation_report.md), pilot candidates were inspected during query formulation, so the 4/4 pilot success cannot be interpreted as a generalizable holdout rate.
2. **Context Presence vs. Claim Synthesis**: In 19 of 26 questions, approved answer pages were present in the final generation context passed to the LLM. However, compound reasoning requirements frequently led the generator to omit secondary claims or adopt cautious refusal phrasing despite having supporting passages available.
3. **Missing Approved Pages**: In 7 questions (`Q005`, `Q006`, `Q008`, `Q009`, `Q011`, `Q020`, `Q022`), the pipeline failed to deliver the approved physical page into the final generation context due to upstream retrieval or reranker cutoffs.
4. **Citations Require Verification**: Citations emitted in answers reflect retrieved context passages and are not guaranteed to be complete or accurate; development generation achieved only a 2/22 (9.1%) human acceptance rate, and all outputs require independent verification against original source PDFs.
5. **Corpus & Reproduction Boundaries**: The reported benchmark was evaluated against a local corpus of 66 academic research papers (7,816 chunks) stored in a local ChromaDB vector index and BM25 cache. Under copyright and storage hygiene, PDF source files and binary index caches are excluded from this source repository; a clean clone does not reproduce historical numbers without ingesting the corpus.

For full methodologies, partitioned metrics, and cryptographic provenance, consult:
- [Pipeline Evaluation & Benchmark Report](docs/evaluation/evaluation_report.md)
- Canonical Benchmark: [`docs/evaluation/phase4_questions.json`](docs/evaluation/phase4_questions.json)
- Authoritative Signed Evidence Forms & Frozen Worksheets: Preserved in private archive with verified SHA-256 hashes recorded in [`docs/evaluation/evaluation_report.md`](docs/evaluation/evaluation_report.md).

---

## Security & Operational Scope

- **Local-Only Single-User Application**: CiteFirst is designed for local desktop and workstation use. The FastAPI backend binds strictly to `127.0.0.1`.
- **Unauthenticated API**: The API contains no user authentication or multi-tenant access control. It must **not** be exposed directly to untrusted public networks without an authenticating reverse proxy.
- **Privacy & Secret Protection**: No external analytics or telemetry are transmitted. API keys are loaded via local `.env` and excluded from source control.

---

## Lineage, Permissions, & Licensing

- **Lineage**: CiteFirst originated from the CRAG-Pipeline group project created at Manipal Institute of Technology by **Sushant Shekhar Sinha**, **Kanan Gupta**, and **Qusai**. See [`NOTICE.md`](NOTICE.md) for full historical credit.
- **Contributor Permissions**: Written permission has been received from both original co-authors (Sushant Shekhar Sinha and Kanan Gupta) to copy, modify, redistribute, and publicly release their original contributions as part of CiteFirst with authorship credit.
- **License Status**: Selection of the exact SPDX license identifier for CiteFirst's original project code remains under review (proposed choice: `AGPL-3.0-or-later` subject to final audit of PyMuPDF dependencies and asset licenses). There is currently no root `LICENSE` file installed; license selection is pending until finalized.
- **Third-Party Materials**: All research papers, model weights, and upstream library dependencies remain governed by their respective original copyright holders and licenses.
