# CRAG — Corrective Retrieval-Augmented Generation

A full-stack RAG (Retrieval-Augmented Generation) application with a **4-phase corrective pipeline** for answering questions from academic PDF papers. Retrieved passages and source PDF pages are shown for inspection; an answer or status label is not a guarantee of factual accuracy.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Next.js 16 Frontend                      │
│         (app/, components/, hooks/, lib/, types/)           │
├─────────────────────────────────────────────────────────────┤
│                   FastAPI REST Bridge                       │
│                       (api.py)                              │
├─────────────────────────────────────────────────────────────┤
│              Python Backend Pipeline                        │
│   database.py ─► logic_engine.py ─► evaluator.py           │
│   (ChromaDB)     (4-Phase CRAG)     (LLM Grader)           │
├─────────────────────────────────────────────────────────────┤
│                   ChromaDB Vector Store                     │
│                    (vector_vault/)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## Backend Pipeline (4 Phases)

### Phase 1 — Hybrid Retrieval (Dense + BM25 + RRF)

- **Embedding Model**: `BAAI/bge-small-en-v1.5` (384 dimensions)
- Newly ingested PDFs are chunked into **sentence-level child chunks** and **semantic parent chunks** within each PDF page
- Retrieval uses **dense vector search** (ChromaDB) + **BM25 sparse search** fused via **Reciprocal Rank Fusion (RRF)**
- Parent expansion: child chunks are scored, but parent chunks are sent to the LLM for richer context
- **`FETCH_K=30`** chunks are fetched, filtered by a cosine distance threshold

### Phase 2 — BGE Reranker (Cross-Encoder Scoring)

- **Reranker Model**: `BAAI/bge-reranker-base` (cross-encoder)
- All fetched chunks are re-scored with query-document cross-attention
- Top **`PROCESS_K=10`** chunks are kept for grading
- Scores are converted via sigmoid to `[0, 1]` probabilities

### Phase 3 — Tri-State Grading + Pre-Flight Check

- Each chunk is graded into **3 tiers** based on sigmoid-scale thresholds:
  - **Correct** (≥ 0.55): High-confidence relevant chunks
  - **Ambiguous** (≥ 0.25): Potentially relevant, needs verification
  - **Incorrect** (< 0.25): Discarded
- **Ambiguous Resolution**: Ambiguous chunks undergo verification by the configured generation provider
- **Pre-Flight Check**: An LLM checks whether the combined verified passages answer the query; a failed check triggers a rewritten query against the vault. `SOFTMAX_MASS_CUTOFF` (0.90) controls a separate candidate-pruning step.

### Phase 4 — Answer Generation (LLM)

- **LLM**: Groq API (`llama-3.3-70b-versatile` by default) or local Ollama
- Only verified chunks (correct + resolved-ambiguous) are sent as context
- The LLM generates an answer grounded in the provided chunks
- Response includes: answer text, source metadata and page evidence when available, chunk grades, pipeline status

### Pipeline Status Outcomes

| Status | Meaning |
|--------|---------|
| `success` | ≥1 correct chunk, answer generated from vault |
| `fallback_success` | A rewritten query found usable vault evidence |
| `partial_match` | Only related vault passages were found; the answer labels the match as partial |
| `failed` | No passage met the pipeline's thresholds |

---

## Backend Files

| File | Purpose |
|------|---------|
| `api.py` | FastAPI REST API bridge — connects the Next.js frontend to the Python pipeline. Handles streaming SSE, file uploads, settings CRUD, vault management, and evaluation triggers. |
| `database.py` | ChromaDB vector store management — page-scoped PDF ingestion (sentence + semantic chunking), hybrid search (dense + BM25 + RRF), parent-child expansion, and vault CRUD operations. |
| `logic_engine.py` | The core 4-phase CRAG pipeline — reranking, tri-state grading, ambiguous resolution via LLM, pre-flight relevance check, and final answer generation. |
| `providers.py` | Groq and Ollama generation requests. |
| `settings_config.py` | Shared defaults and compatibility for stored settings. |
| `evaluator.py` | Evidence-gated, LLM-free hybrid document retrieval audit and metrics; excludes unverified candidates. |
| `generate_dataset.py` | Golden dataset generator — creates Q&A pairs from the ingested papers for evaluation. |
| `upload_papers.py` | Batch PDF ingestion script — processes all PDFs in the `papers/` directory into ChromaDB. |
| `test_search.py` | Quick search test — verifies that the vector store retrieval is working. |
| `settings.json` | Runtime configuration — thresholds, chunk limits, and pipeline parameters (hot-reloadable via the Settings page). |
| `requirements.txt` | Python dependencies. |

---

## Frontend Pages

| Route | Page | Description |
|-------|------|-------------|
| `/` | Home | Landing page with pipeline overview, metrics preview, and quick-query bar |
| `/chat` | Chat | Interactive Q&A interface with PDF upload, file-scoped filtering, streaming responses, chunk visualization, and PDF export |
| `/pipeline` | Pipeline | Real-time pipeline visualizer showing each phase as chunks flow through |
| `/analytics` | Analytics | Evidence-gated hybrid document retrieval audit, coverage counts, and ranked metrics when verified labels exist |
| `/vault` | Vault | Document management — view/delete/search ingested PDFs, see chunk counts |
| `/settings` | Settings | Hot-reload pipeline thresholds (CORRECT, AMBIGUOUS, BENDY, distance, etc.) |

---

## Prerequisites

- **Python 3.10+** with pip
- **Node.js 22** with npm (used by CI)
- **Groq API key** for the default provider, or an already running Ollama server and downloaded model

---

## How to Run

### 1. Clone and setup environment

```bash
cd CRAG

# Create Python virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Configure the generation provider

Copy the example environment file and add a Groq API key for the default provider:

```bash
cp .env.example .env
```

Then edit `.env` and replace `your_groq_api_key_here` with your actual key from [console.groq.com](https://console.groq.com):

```
GROQ_API_KEY=your_key_from_groq
```

For a locally running Ollama service, set `LLM_PROVIDER=ollama` and configure
`OLLAMA_BASE_URL` and `OLLAMA_MODEL` in `.env`. Ollama mode does not need a Groq
key. The default local model name is `llama3.1:8b`; it must already be available
in Ollama. A first model download generally needs internet, and local inference
needs sufficient RAM and CPU. Provider requests have a finite timeout; this
stage does not support provider token streaming. The default remains Groq.

### 3. Ingest PDF papers

Create a `papers/` directory and place your PDF documents in it:

```bash
mkdir papers
# Add your PDF files to the papers/ folder
```

Then ingest them into the vector store:

```bash
python upload_papers.py
```

This will chunk and embed all PDFs into the ChromaDB vector store (`vector_vault/` by default). The first query may download the embedding and reranking models; reserve disk space, memory, and CPU for local model inference.

### 4. Install frontend dependencies

```bash
npm ci
```

### 5. Start both servers

Open **two terminals** in the project root:

**Terminal 1 — Backend API (port 8000):**
```bash
uvicorn api:app --reload --host 127.0.0.1 --port 8000
```

**Terminal 2 — Frontend (port 3000):**
```bash
npm run dev
```

### 6. Open the app

Navigate to **http://localhost:3000** in your browser. Source cards open the original PDF at a one-based PDF page number when the selected index has page metadata. Exact passage highlighting is not available in the browser PDF viewer; older indexes display “page unavailable”. Pipeline stages reflect backend events, and the status describes the pipeline path, not verified truth.

### Local access boundary

The documented backend command and the frontend `dev` and `start` scripts bind
to loopback (`127.0.0.1`). Use the app on a trusted machine. The API endpoints
for document upload, listing and deletion, evaluation, and settings are
**unauthenticated**. CORS restricts browser origins but does not authenticate
clients. Do not expose the API or frontend to an untrusted network, forward its
ports, or deploy it publicly without a deliberate authentication and deployment
design. A custom command or container port mapping can bypass these loopback
defaults.

Backend settings are read from `settings.json`, with missing keys supplied by
`settings_config.py`. An existing, unmarked settings file keeps the historical
legacy-vault grading bars (0.52/0.22); a new vault uses 0.55/0.25. Saving from
the Settings page marks the file as customized, so its selected thresholds take
effect for either vault schema. The distance threshold is read for each search,
and API saves hot-reload the logic engine settings. The frontend's local defaults
are only a fallback when the API cannot be reached.

Old `vector_vault/bm25_corpus.pkl` files are never loaded or deleted by the app.
The first BM25 search rebuilds a versioned `bm25_corpus.json` in the selected
vector directory from the existing Chroma document collection. Keep the legacy
cache until you have checked the rebuilt index; no vector store or source PDFs
need to be removed.

### Page-aware index migration

New ingestion keeps parent and child chunks within PDF page boundaries and stores
a zero-based `page_index` with each chunk. Existing indexes have no reliable page
metadata. To build a new index without overwriting the current one, keep the
existing `vector_vault/` and `papers/` directories, then run:

```bash
CITEFIRST_VECTOR_DIR=./vector_vault_page_v1 python database.py
CITEFIRST_VECTOR_DIR=./vector_vault_page_v1 uvicorn api:app --host 127.0.0.1 --port 8000
```

Set the same variable for later API starts; omit it to roll back to the original
index. A newly uploaded paper is indexed into the selected directory. Rebuilds
use the existing PyMuPDF text extraction and append detected tables as Markdown
for inspection. We evaluated PyMuPDF4LLM 1.28.2 with `page_chunks=True` on a
two-page sample: its metadata supplied one-based `page_number` values. It is
not added to the project dependencies because its AGPL/commercial terms and the
separate PyMuPDF Layout license need a distribution decision. The current
PyMuPDF dependency also has licensing implications for distribution. See the
[PyMuPDF4LLM API](https://pymupdf.readthedocs.io/en/latest/pymupdf4llm/api.html)
and [license notes](https://github.com/pymupdf/pymupdf4llm/blob/main/CHANGES.md).

---

## Optional: Run Evaluation

To audit the candidate dataset without a model or API key:

```bash
python evaluator.py --audit-only
```

Once human-verified paper/page evidence has been added to a reviewed copy:

```bash
python evaluator.py --dataset reviewed_dataset.json --index-tag "my-fixed-index"
```

This scores every eligible answerable question using hybrid retrieval before CRAG and writes ignored `evaluation_results/` reports. Paper ranks are deduplicated within the first ten retrieved chunks, which may contain fewer than ten unique papers. The checked-in 18 DeepSeek candidates have no verified evidence, so the current baseline is blocked. A scored run requires a fixed index tag, local index and embedding model, but no Groq/Ollama credentials; answer and citation quality need separate review. The home and analytics pages do not advertise the old unverified accuracy/F1 values. See [Phase 3 audit](docs/evaluation/phase3-audit.md), [methodology](docs/evaluation/methodology.md), and [annotation worksheet](docs/evaluation/annotation-template.md).

---

## Project Structure

```
CRAG/
├── app/                    # Next.js App Router pages
│   ├── layout.tsx          # Root layout with navigation
│   ├── page.tsx            # Home page
│   ├── globals.css         # Design tokens + global styles
│   ├── chat/               # Chat page
│   ├── pipeline/           # Pipeline visualizer page
│   ├── analytics/          # Analytics dashboard page
│   ├── vault/              # Vault management page
│   └── settings/           # Settings page
├── components/             # React UI components
│   ├── chat/               # ChatInterface, ChatBubble
│   ├── home/               # HeroSection, PipelineSection, MetricsPreview
│   ├── pipeline/           # PipelineVisualizer
│   ├── analytics/          # AnalyticsDashboard
│   ├── vault/              # VaultManager
│   ├── settings/           # SettingsPanel
│   ├── layout/             # Navbar, ThemeProvider
│   └── ui/                 # Shared UI primitives
├── hooks/                  # React hooks (useChatHistory, useEvaluation)
├── lib/                    # API client, constants
├── types/                  # TypeScript type definitions
├── public/                 # Static assets
├── api.py                  # FastAPI backend bridge
├── database.py             # ChromaDB vector store + hybrid search
├── logic_engine.py         # 4-phase CRAG pipeline
├── evaluator.py            # Evaluation framework
├── generate_dataset.py     # Golden dataset generator
├── upload_papers.py        # Batch PDF ingester
├── test_search.py          # Search verification script
├── settings.json           # Pipeline configuration
├── golden_dataset.json     # Evaluation Q&A pairs
├── requirements.txt        # Python dependencies
├── package.json            # Node.js dependencies
├── tsconfig.json           # TypeScript config
├── next.config.ts          # Next.js config
├── papers/                 # PDF documents (input)
├── vector_vault/           # ChromaDB storage (auto-generated)
└── .env                    # API keys (not committed)
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4, Radix UI, Motion (Framer), Recharts |
| Backend API | FastAPI, Uvicorn, SSE (Server-Sent Events) |
| Vector Store | ChromaDB (persistent, on-disk) |
| Embeddings | `BAAI/bge-small-en-v1.5` (sentence-transformers) |
| Reranker | `BAAI/bge-reranker-base` (cross-encoder) |
| LLM | Groq (`llama-3.3-70b-versatile`) or Ollama (`llama3.1:8b` by default) |
| Sparse Search | BM25 via `rank_bm25` (optional) |
| PDF Parsing | PyMuPDF (`fitz`) |

---

## Checks

The model-free regression suite runs without API keys, papers, or downloaded ML models:

```bash
python -m pip install -r requirements-test.txt
python -m pytest -q tests
npm ci
npm run lint
npx tsc --noEmit
npm run build
```

GitHub Actions runs these checks on pushes and pull requests. The backend suite uses a minimal test dependency list; a live Groq/Ollama call, full-model ingestion and retrieval, and an evaluation run need the production dependencies and local resources. The historical metric values previously shown here were not reproduced during this phase; formal evaluation remains future work.

---

## License

See `NOTICE.md` for the original group-project authorship. The repository has no explicit project license grant in its tracked files, and permission to relicense the inherited code has not been established. Maintainers should resolve ownership and distribution terms before publishing a release; an educational/research description is not a license. Dependency licenses also apply, including the existing PyMuPDF terms.
