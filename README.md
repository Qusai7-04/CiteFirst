# CRAG — Corrective Retrieval-Augmented Generation

A full-stack RAG (Retrieval-Augmented Generation) intelligence platform that implements a **4-phase corrective pipeline** for answering questions from academic PDF papers with high accuracy.

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

- **Embedding Model**: `BAAI/bge-small-en-v1.5` (384-dim, high-accuracy)
- PDFs are chunked into **sentence-level child chunks** and **semantic parent chunks**
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
- **Ambiguous Resolution**: Ambiguous chunks undergo Groq LLM verification — the LLM judges if the chunk actually answers the query
- **Pre-Flight Check**: A combined relevance score from correct + verified-ambiguous chunks must exceed `SOFTMAX_MASS_CUTOFF` (0.90), otherwise the system falls back to web search

### Phase 4 — Answer Generation (LLM)

- **LLM**: Groq API (`llama3-8b-8192`)
- Only verified chunks (correct + resolved-ambiguous) are sent as context
- The LLM generates an answer grounded in the provided chunks
- Response includes: answer text, source metadata, chunk grades, pipeline status

### Pipeline Status Outcomes

| Status | Meaning |
|--------|---------|
| `success` | ≥1 correct chunk, answer generated from vault |
| `fallback_success` | No correct chunks, but ambiguous chunks verified successfully |
| `partial_match` | Some chunks found but pre-flight check failed; web fallback used |
| `failed` | No relevant chunks found at all |

---

## Backend Files

| File | Purpose |
|------|---------|
| `api.py` | FastAPI REST API bridge — connects the Next.js frontend to the Python pipeline. Handles streaming SSE, file uploads, settings CRUD, vault management, and evaluation triggers. |
| `database.py` | ChromaDB vector store management — PDF ingestion (sentence + semantic chunking), hybrid search (dense + BM25 + RRF), parent-child chunk expansion, and vault CRUD operations. |
| `logic_engine.py` | The core 4-phase CRAG pipeline — reranking, tri-state grading, ambiguous resolution via LLM, pre-flight relevance check, and final answer generation with Groq. |
| `evaluator.py` | Evaluation framework — runs the pipeline against `golden_dataset.json`, computes precision/recall/F1/accuracy using an LLM grader, and generates metric charts + confusion matrices. |
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
| `/analytics` | Analytics | Evaluation dashboard with precision/recall/F1 gauges, confusion matrices, and pipeline configuration summary |
| `/vault` | Vault | Document management — view/delete/search ingested PDFs, see chunk counts |
| `/settings` | Settings | Hot-reload pipeline thresholds (CORRECT, AMBIGUOUS, BENDY, distance, etc.) |

---

## Prerequisites

- **Python 3.10+** with pip
- **Node.js 18+** with npm
- **Groq API Key** (free at [console.groq.com](https://console.groq.com))

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

### 2. Configure API key

Copy the example environment file and add your Groq API key:

```bash
cp .env.example .env
```

Then edit `.env` and replace `your_groq_api_key_here` with your actual key from [console.groq.com](https://console.groq.com):

```
GROQ_API_KEY=gsk_your_actual_key_here
```

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

This will chunk and embed all PDFs into the ChromaDB vector store (`vector_vault/`).

### 4. Install frontend dependencies

```bash
npm install
```

### 5. Start both servers

Open **two terminals** in the project root:

**Terminal 1 — Backend API (port 8000):**
```bash
uvicorn api:app --reload --port 8000
```

**Terminal 2 — Frontend (port 3000):**
```bash
npm run dev
```

### 6. Open the app

Navigate to **http://localhost:3000** in your browser.

---

## Optional: Run Evaluation

To evaluate the pipeline against the golden dataset:

```bash
python evaluator.py
```

This will:
1. Run every question in `golden_dataset.json` through the pipeline
2. Grade answers using an LLM grader
3. Generate metric charts (`metrics_chart_*.png`) and confusion matrices (`confusion_matrix_*.png`)
4. Print precision, recall, F1, and accuracy scores

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
| LLM | Groq (`llama3-8b-8192`) |
| Sparse Search | BM25 via `rank_bm25` (optional) |
| PDF Parsing | PyMuPDF (`fitz`) |

---

## Evaluation Results

| Metric | Value |
|--------|-------|
| Precision | 65% |
| Recall | 81% |
| F1 Score | 0.72 |
| Accuracy | 98% |

Confusion matrix: TP=13, FP=7, FN=3, TN=570

---

## License

This project is for educational/research purposes.
