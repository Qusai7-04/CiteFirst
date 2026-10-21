"""
Independent verification script for frozen 30-candidate reranking audit.
Evaluates Q001-Q018 on explicitly identical 30-candidate pool before and after
cross-encoder reranking (BAAI/bge-reranker-base).
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
from phase4_diagnostics import rerank_fixed_candidates, first_rank, describe_pool

INDEX_DIR = ROOT / "vector_vault_eval"
os.environ["CITEFIRST_VECTOR_DIR"] = str(INDEX_DIR.resolve())
from database import search_vault

def run_frozen_audit():
    dataset_path = ROOT / "reviewed_dataset.json"
    records, digest = load_dataset(dataset_path)
    audited = audit_records(records)

    results = []
    print(f"Starting frozen 30-candidate audit for {len(records)} questions...")

    for i, (rec, aud) in enumerate(zip(records, audited)):
        qid = aud["id"]
        gold_paper = aud["gold_papers"][0]
        approved_pages = {(e["source_filename"], e["page"]) for e in aud["evidence"] if e.get("page") is not None}

        trace = {}
        t0 = time.perf_counter()
        raw = search_vault(rec["question"], n_results=30, trace=trace, candidate_source="hybrid")

        # Sliced 30 candidate pool
        expanded_30 = trace["expanded"][:30]
        prerank_pool = describe_pool(expanded_30, gold_paper)
        prerank_paper_rank = prerank_pool["paper_rank"]

        # Candidate IDs checksum
        cand_ids = [m.get("chunk_id") for m in raw["metadatas"][0][:30] if m]
        cand_sha256 = hashlib.sha256(json.dumps(cand_ids).encode()).hexdigest()

        # Cross-encoder rerank on the identical 30 candidates
        rerank_res = rerank_fixed_candidates(rec["question"], raw, candidate_pool=30)
        t_rerank = rerank_res["timing_seconds"]

        ranked_items = rerank_res["ranked"]
        distinct_papers = list(dict.fromkeys(item["source_filename"] for item in ranked_items if item.get("source_filename")))
        post_rank = distinct_papers.index(gold_paper) + 1 if gold_paper in distinct_papers else None
        first_chunk_rank = first_rank(ranked_items, gold_paper)

        first_approved = next((idx for idx, item in enumerate(ranked_items, 1)
                               if (item.get("source_filename"), item.get("page")) in approved_pages), None)
        survive_process_k = any((item.get("source_filename"), item.get("page")) in approved_pages
                                for item in rerank_res["process_k"])
        survive_adaptive = any((item.get("source_filename"), item.get("page")) in approved_pages
                               for item in rerank_res["adaptive"])

        item = {
            "id": qid,
            "candidate_count": len(cand_ids),
            "candidate_ids_sha256": cand_sha256,
            "pre_rank": prerank_paper_rank,
            "post_rank": post_rank,
            "first_chunk_rank": first_chunk_rank,
            "first_approved_page_rank": first_approved,
            "survive_process_k": bool(survive_process_k),
            "survive_adaptive": bool(survive_adaptive),
            "rerank_time_seconds": t_rerank
        }
        results.append(item)
        print(f"[{i+1}/18] {qid}: Pre={prerank_paper_rank} -> Post={post_rank} | ApprPageRank={first_approved} (in {t_rerank:.2f}s)")

    out_path = ROOT / "evaluation_results/frozen_30_rerank_audit.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")

    latencies = [r["rerank_time_seconds"] for r in results]
    mean_lat = sum(latencies) / len(latencies)
    print(f"\nAudit complete. Wrote {out_path}.")
    print(f"Mean rerank latency: {mean_lat:.2f}s")
    print(f"Post-rerank rank 1: {sum(r['post_rank'] == 1 for r in results)}/18")
    print(f"Survive PROCESS_K: {sum(r['survive_process_k'] for r in results)}/18")

if __name__ == "__main__":
    run_frozen_audit()
