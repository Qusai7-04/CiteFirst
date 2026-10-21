"""
Observational initial-stage simulation of the normal CiteFirst retrieval and reranking path.
Simulates initial retrieval, cross-encoder reranking, adaptive selection, and initial CORRECT/AMBIGUOUS grading.
Does NOT execute full logic_engine.run_logic_engine control flow (ambiguous resolution, supplemental search,
preflight LLM check, query rewrite, or final answer generation).
Measurements (e.g. 14/18 approved page in initial context, initial no-CORRECT count, and stage latency)
represent initial-stage simulation, not final generation success.
"""
import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from evaluation.dataset import audit_records, load_dataset
from settings_config import load_settings

INDEX_DIR = ROOT / "vector_vault_eval"
os.environ["CITEFIRST_VECTOR_DIR"] = str(INDEX_DIR.resolve())

from database import search_vault
from logic_engine import (
    _get_reranker, _trim, _adaptive_select, _sigmoid,
    PROCESS_K, CORRECT_THRESHOLD, AMBIGUOUS_THRESHOLD,
    MAX_VERIFIED_CHUNKS, SOFTMAX_MASS_CUTOFF
)

def run_observational_capture():
    settings = load_settings()
    dataset_path = ROOT / "reviewed_dataset.json"
    records, digest = load_dataset(dataset_path)
    audited = audit_records(records)

    trace_records = []
    print(f"Starting normal production path observation for {len(records)} questions...")

    for i, (rec, aud) in enumerate(zip(records, audited)):
        qid = aud["id"]
        qtext = rec["question"]
        gold_paper = aud["gold_papers"][0]
        approved_pages = {(e["source_filename"], e["page"]) for e in aud["evidence"] if e.get("page") is not None}

        t0 = time.perf_counter()

        # Step 1: Normal production retrieval with n_results=30 (FETCH_K)
        retrieval_trace = {}
        raw = search_vault(qtext, n_results=30, trace=retrieval_trace, candidate_source="hybrid")
        t_retrieval = time.perf_counter() - t0

        raw_chunks = raw["documents"][0]
        raw_metas = raw["metadatas"][0]
        actual_returned_count = len(raw_chunks)

        # Raw first paper rank and approved page rank
        raw_papers = [m.get("source") for m in raw_metas if m]
        distinct_raw_papers = list(dict.fromkeys(raw_papers))
        raw_paper_rank = distinct_raw_papers.index(gold_paper) + 1 if gold_paper in distinct_raw_papers else None

        raw_approved_page_rank = next((idx for idx, m in enumerate(raw_metas, 1)
                                      if (m.get("source"), (m.get("page_index") + 1 if isinstance(m.get("page_index"), int) and m.get("page_index") >= 0 else None)) in approved_pages), None)

        # Step 2: evaluate_chunks scoring with BAAI/bge-reranker-base (batched for performance)
        t_eval_start = time.perf_counter()
        has_child = any(m.get("child_text") for m in raw_metas if m)
        pairs = []
        item_data = []
        for doc_chunk, meta in zip(raw_chunks, raw_metas):
            source = meta.get("source", "Unknown") if meta else "Unknown"
            score_text = meta.get("child_text", doc_chunk) if (has_child and meta) else doc_chunk
            pairs.append([qtext, _trim(score_text)])
            item_data.append((doc_chunk, source, score_text, meta))

        raw_logits = _get_reranker().predict(pairs, batch_size=32)
        scored = []
        for logit, (doc_chunk, source, score_text, meta) in zip(raw_logits, item_data):
            scored.append((float(logit), doc_chunk, source, score_text, meta))

        scored.sort(key=lambda x: x[0], reverse=True)
        actual_reranked_count = len(scored)

        # Reranked paper rank & approved page rank
        reranked_papers = list(dict.fromkeys(s[2] for s in scored))
        reranked_paper_rank = reranked_papers.index(gold_paper) + 1 if gold_paper in reranked_papers else None
        reranked_approved_page_rank = next((idx for idx, s in enumerate(scored, 1)
                                            if (s[2], (s[4].get("page_index") + 1 if isinstance(s[4].get("page_index"), int) and s[4].get("page_index") >= 0 else None)) in approved_pages), None)

        top_candidates = scored[:PROCESS_K]

        # Adaptive softmax selection
        softmax_input = [(r, c, s, m) for r, c, s, _, m in top_candidates]
        adaptive_pool = _adaptive_select(softmax_input)

        # Tri-state grading
        grades = []
        verified_chunks = []
        verified_sources = []
        verified_metas = []

        for sigmoid_score, chunk, source, meta in adaptive_pool:
            if sigmoid_score >= CORRECT_THRESHOLD:
                grade = "CORRECT"
                verified_chunks.append(chunk)
                verified_sources.append(source)
                verified_metas.append(meta)
            elif sigmoid_score >= AMBIGUOUS_THRESHOLD:
                grade = "AMBIGUOUS"
            else:
                grade = "INCORRECT"
            grades.append({
                "source": source,
                "page": meta.get("page_index") + 1 if isinstance(meta.get("page_index"), int) and meta.get("page_index") >= 0 else None,
                "sigmoid_score": round(sigmoid_score, 4),
                "grade": grade
            })

        # Hard cap MAX_VERIFIED_CHUNKS (4)
        if len(verified_chunks) > MAX_VERIFIED_CHUNKS:
            verified_chunks = verified_chunks[:MAX_VERIFIED_CHUNKS]
            verified_sources = verified_sources[:MAX_VERIFIED_CHUNKS]
            verified_metas = verified_metas[:MAX_VERIFIED_CHUNKS]

        t_eval = time.perf_counter() - t_eval_start

        # Fallback decision
        fallback_triggered = len(verified_chunks) == 0

        # Selected generation context (text that would be fed to generate_final_answer)
        generation_context = [
            {
                "source": src,
                "page": m.get("page_index") + 1 if isinstance(m.get("page_index"), int) and m.get("page_index") >= 0 else None,
                "chunk_id": m.get("chunk_id"),
                "text": chk
            }
            for chk, src, m in zip(verified_chunks, verified_sources, verified_metas)
        ]

        approved_in_verified = any((ctx["source"], ctx["page"]) in approved_pages for ctx in generation_context)

        trace_record = {
            "id": qid,
            "question": qtext,
            "gold_paper": gold_paper,
            "approved_pages": list(approved_pages),
            "actual_returned_count": actual_returned_count,
            "actual_reranked_count": actual_reranked_count,
            "raw_paper_rank": raw_paper_rank,
            "raw_approved_page_rank": raw_approved_page_rank,
            "reranked_paper_rank": reranked_paper_rank,
            "reranked_approved_page_rank": reranked_approved_page_rank,
            "adaptive_pool_size": len(adaptive_pool),
            "grade_counts": {
                "CORRECT": sum(1 for g in grades if g["grade"] == "CORRECT"),
                "AMBIGUOUS": sum(1 for g in grades if g["grade"] == "AMBIGUOUS"),
                "INCORRECT": sum(1 for g in grades if g["grade"] == "INCORRECT")
            },
            "grades": grades,
            "verified_chunks_count": len(verified_chunks),
            "approved_passage_in_verified_context": approved_in_verified,
            "fallback_triggered": fallback_triggered,
            "selected_generation_context": generation_context,
            "llm_generation_status": "NOT RUN — requires a configured live provider",
            "timing_seconds": {
                "retrieval": round(t_retrieval, 4),
                "evaluation": round(t_eval, 4),
                "total": round(t_retrieval + t_eval, 4)
            }
        }
        trace_records.append(trace_record)
        print(f"[{i+1}/18] {qid}: RawCount={actual_returned_count} -> Reranked={actual_reranked_count} | PostRank={reranked_paper_rank} | Verified={len(verified_chunks)} (Appr={approved_in_verified}) in {t_retrieval+t_eval:.2f}s")

    out_file = ROOT / "evaluation_results/normal_production_path_trace.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)

    result = {
        "description": "Observational initial-stage simulation of retrieval, reranking, and chunk grading (does not execute full logic_engine control flow or answer generation)",
        "configuration": {
            "FETCH_K": 30,
            "PROCESS_K": PROCESS_K,
            "SOFTMAX_MASS_CUTOFF": SOFTMAX_MASS_CUTOFF,
            "CORRECT_THRESHOLD": CORRECT_THRESHOLD,
            "AMBIGUOUS_THRESHOLD": AMBIGUOUS_THRESHOLD,
            "MAX_VERIFIED_CHUNKS": MAX_VERIFIED_CHUNKS,
            "reranker_model": "BAAI/bge-reranker-base"
        },
        "records": trace_records
    }
    out_file.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"\nSaved normal production path trace to {out_file}")

if __name__ == "__main__":
    run_observational_capture()
