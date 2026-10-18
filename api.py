"""
FastAPI bridge between Next.js frontend and the CRAG Python pipeline.
Run with: uvicorn api:app --reload --port 8000
"""
import json
import os
import uuid
import time
import asyncio
import threading
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI(title="CRAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="."), name="static")

# ── Settings file path ────────────────────────────────────────────────────────
SETTINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")


def _load_settings() -> dict:
    defaults = {
        "FETCH_K": 30, "PROCESS_K": 10, "CHUNK_WORD_LIMIT": 300,
        "CORRECT_THRESHOLD": 0.55, "AMBIGUOUS_THRESHOLD": 0.25,
        "BENDY_THRESHOLD": 0.10, "MAX_VERIFIED_CHUNKS": 2,
        "SOFTMAX_MASS_CUTOFF": 0.90, "DISTANCE_THRESHOLD": 0.70,
        "TOTAL_DOCS": 60,
    }
    try:
        with open(SETTINGS_PATH, "r") as f:
            defaults.update(json.load(f))
    except FileNotFoundError:
        pass
    return defaults


def _save_settings(data: dict):
    with open(SETTINGS_PATH, "w") as f:
        json.dump(data, f, indent=2)


# ── Lazy-load CRAG modules ───────────────────────────────────────────────────
try:
    from logic_engine import run_logic_engine, reload_config  # type: ignore
    from evaluator import run_ml_evaluation  # type: ignore
    from database import process_and_save_pdf, delete_document, list_documents  # type: ignore
    CRAG_AVAILABLE = True
except Exception as e:
    CRAG_AVAILABLE = False
    print(f"[WARN] CRAG modules not loaded: {e}. Stub responses will be returned.")


# ── Pydantic models ──────────────────────────────────────────────────────────
class QueryRequest(BaseModel):
    question: str
    file_filter: Optional[str] = None


class SettingsPayload(BaseModel):
    FETCH_K: int = 30
    PROCESS_K: int = 10
    CHUNK_WORD_LIMIT: int = 300
    CORRECT_THRESHOLD: float = 0.55
    AMBIGUOUS_THRESHOLD: float = 0.25
    BENDY_THRESHOLD: float = 0.10
    MAX_VERIFIED_CHUNKS: int = 2
    SOFTMAX_MASS_CUTOFF: float = 0.90
    DISTANCE_THRESHOLD: float = 0.70
    TOTAL_DOCS: int = 60


# ── In-memory evaluation task store ──────────────────────────────────────────
_eval_tasks: dict[str, dict] = {}


# ── Health ───────────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {"status": "ok", "crag_available": CRAG_AVAILABLE}


# ── Query (non-streaming) ───────────────────────────────────────────────────
@app.post("/api/query")
def query(req: QueryRequest):
    if not CRAG_AVAILABLE:
        return {
            "status": "success",
            "answer": f"[STUB] Backend modules not loaded. Query: {req.question}",
            "facts": [], "sources": [], "query_used": req.question,
        }
    try:
        import database as _db
        # Apply file filter scoped to this call
        prev = getattr(_db, "_ACTIVE_FILE_FILTER", None)
        if req.file_filter:
            _db._ACTIVE_FILE_FILTER = req.file_filter
        try:
            result = run_logic_engine(req.question)
        finally:
            _db._ACTIVE_FILE_FILTER = prev
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Query (SSE streaming) ───────────────────────────────────────────────────
@app.post("/api/query/stream")
async def query_stream(req: QueryRequest):
    """
    Server-Sent Events endpoint.
    Emits simulated pipeline progress steps, then the real result.
    """
    async def event_generator():
        steps = [
            {"step": "fetching", "detail": "Hybrid retrieval (Dense + BM25 + RRF)", "progress": 15},
            {"step": "reranking", "detail": "BGE Reranker cross-encoder scoring", "progress": 35},
            {"step": "grading", "detail": "Tri-state grading: CORRECT / AMBIGUOUS / INCORRECT", "progress": 55},
            {"step": "resolving", "detail": "Pre-flight combined relevance check", "progress": 70},
            {"step": "generating", "detail": "Generating final answer with LLM", "progress": 90},
        ]

        # Emit progress steps with small delays
        for s in steps:
            yield f"data: {json.dumps(s)}\n\n"
            await asyncio.sleep(0.4)

        # Run the actual pipeline
        if CRAG_AVAILABLE:
            try:
                import database as _db
                prev = getattr(_db, "_ACTIVE_FILE_FILTER", None)
                if req.file_filter:
                    _db._ACTIVE_FILE_FILTER = req.file_filter
                try:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, run_logic_engine, req.question)
                finally:
                    _db._ACTIVE_FILE_FILTER = prev
            except Exception as e:
                result = {
                    "status": "failed",
                    "answer": f"Pipeline error: {str(e)}",
                    "facts": [], "sources": [], "query_used": req.question,
                }
        else:
            result = {
                "status": "success",
                "answer": f"[STUB] Backend modules not loaded. Query: {req.question}",
                "facts": [], "sources": [], "query_used": req.question,
            }

        done_event = {"step": "done", "progress": 100, "result": result}
        yield f"data: {json.dumps(done_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Evaluation (async task) ──────────────────────────────────────────────────
@app.post("/api/evaluate")
def start_evaluation():
    task_id = str(uuid.uuid4())
    _eval_tasks[task_id] = {"status": "pending", "result": None}

    def run_eval():
        _eval_tasks[task_id]["status"] = "running"
        try:
            if CRAG_AVAILABLE:
                all_results = run_ml_evaluation()
                if all_results:
                    # New evaluator returns {grader_label: {tp, fp, fn, tn, precision, ...}}
                    # Find the LLM grader key
                    llm_key = next((k for k in all_results if "llm" in k.lower()), None)
                    llm_data = all_results.get(llm_key, {}) if llm_key else {}

                    _eval_tasks[task_id]["status"] = "completed"
                    _eval_tasks[task_id]["result"] = {
                        "precision": llm_data.get("precision", 0),
                        "recall": llm_data.get("recall", 0),
                        "f1": llm_data.get("f1", 0),
                        "accuracy": llm_data.get("accuracy", 0),
                        "llm": {
                            "precision": llm_data.get("precision", 0),
                            "recall": llm_data.get("recall", 0),
                            "f1": llm_data.get("f1", 0),
                            "accuracy": llm_data.get("accuracy", 0),
                        },
                        "llm_confusion": {
                            "tp": llm_data.get("tp", 0),
                            "fp": llm_data.get("fp", 0),
                            "fn": llm_data.get("fn", 0),
                            "tn": llm_data.get("tn", 0),
                        },
                    }
                else:
                    _eval_tasks[task_id]["status"] = "completed"
                    _eval_tasks[task_id]["result"] = {
                        "message": "Evaluation ran but returned no results.",
                    }
            else:
                time.sleep(3)  # Simulate
                # Stub metrics from metrics_chart_llm_llama3.18binstant.png
                _eval_tasks[task_id]["status"] = "completed"
                _eval_tasks[task_id]["result"] = {
                    "precision": 0.65, "recall": 0.81, "f1": 0.72, "accuracy": 0.98,
                    "llm": {"precision": 0.65, "recall": 0.81, "f1": 0.72, "accuracy": 0.98},
                    "llm_confusion": {"tp": 13, "fp": 7, "fn": 3, "tn": 570},
                }
        except Exception as e:
            _eval_tasks[task_id]["status"] = "failed"
            _eval_tasks[task_id]["result"] = {"error": str(e)}

    thread = threading.Thread(target=run_eval, daemon=True)
    thread.start()

    return {"task_id": task_id}


@app.get("/api/evaluate/{task_id}")
def get_evaluation_status(task_id: str):
    task = _eval_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


# ── Vault ────────────────────────────────────────────────────────────────────
@app.get("/api/vault/list")
def vault_list():
    docs = []
    
    # Always scan papers folder
    papers_dir = Path("papers")
    pdf_files = set()
    if papers_dir.exists():
        for f in papers_dir.glob("*.pdf"):
            pdf_files.add(f.name)
            docs.append({
                "id": f.name,
                "filename": f.name,
                "chunks": 0,
                "indexedAt": __import__("datetime").datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                "fileType": "pdf",
                "ingested": False
            })

    if CRAG_AVAILABLE:
        try:
            chroma_docs = list_documents()
            # Mark the ones that are in chroma as ingested
            ingested_sources = {d["filename"] for d in chroma_docs if "filename" in d}
            for d in docs:
                if d["filename"] in ingested_sources:
                    d["ingested"] = True
                    # Let's also update the chunks count from Chroma DB
                    for cd in chroma_docs:
                        if cd["filename"] == d["filename"]:
                            d["chunks"] = cd["chunks"]
                    
            # Add any extra docs from chroma that might not be in the folder
            for d in chroma_docs:
                if d.get("filename") and d["filename"] not in pdf_files:
                    d["ingested"] = True
                    docs.append(d)
        except Exception as e:
            pass # fallback to just the folder list

    return {"documents": docs}


@app.post("/api/vault/upload")
async def vault_upload(file: UploadFile = File(...)):
    papers_dir = Path("papers")
    papers_dir.mkdir(exist_ok=True)
    dest = papers_dir / file.filename
    content = await file.read()
    dest.write_bytes(content)

    # Index in ChromaDB
    if CRAG_AVAILABLE:
        try:
            process_and_save_pdf(str(dest))
        except Exception as e:
            return {"filename": file.filename, "size": len(content), "warning": f"Saved but indexing failed: {e}"}

    return {"filename": file.filename, "size": len(content), "indexed": CRAG_AVAILABLE}


@app.delete("/api/vault/delete/{filename}")
def vault_delete(filename: str):
    # Delete from ChromaDB
    deleted_chunks = 0
    if CRAG_AVAILABLE:
        try:
            deleted_chunks = delete_document(filename)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"ChromaDB delete failed: {e}")

    # Delete physical file
    f = Path("papers") / filename
    if f.exists():
        f.unlink()

    return {"deleted": filename, "chunks_removed": deleted_chunks}


# ── Settings ─────────────────────────────────────────────────────────────────
@app.get("/api/settings")
def get_settings():
    return _load_settings()


@app.put("/api/settings")
def put_settings(payload: SettingsPayload):
    data = payload.model_dump()
    _save_settings(data)

    # Hot-reload the config in logic_engine
    if CRAG_AVAILABLE:
        try:
            reload_config()
        except Exception:
            pass

    return {"status": "saved", "settings": data}
