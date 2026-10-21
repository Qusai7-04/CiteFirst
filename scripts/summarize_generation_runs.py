"""
Summarize real pipeline evaluation runs across Development (N=22) and Held-Out (N=4).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def summarize():
    dev_path = ROOT / "evaluation_results/phase4_dev_generation_results.json"
    pilot_path = ROOT / "evaluation_results/phase4_pilot_generation_results.json"
    if not pilot_path.exists():
        pilot_path = ROOT / "evaluation_results/phase4_held_out_generation_results.json"

    if not dev_path.exists():
        print("Missing development evaluation results file.")
        return

    dev = json.loads(dev_path.read_text(encoding="utf-8"))
    held = json.loads(pilot_path.read_text(encoding="utf-8")) if pilot_path.exists() else None

    dev_records = dev.get("records", [])
    held_records = held.get("records", []) if held else []

    print(f"=== DEVELOPMENT EVALUATION (N={len(dev_records)} across 19 papers) ===")
    dev_top1 = 0
    dev_appr = 0
    dev_status_counts = {}
    for r in dev_records:
        diag = r.get("retrieval_diagnostics") or r.get("retrieval_and_rerank", {})
        boundary = r.get("generation_boundary") or r.get("retrieval_and_rerank", {})
        pe = r.get("pipeline_execution", {})

        raw_rank = diag.get("raw_paper_rank")
        appr_in_ctx = boundary.get("approved_passage_in_final_context") or boundary.get("approved_passage_in_verified_context", False)
        passages_count = boundary.get("verified_context_count") or len(boundary.get("selected_context", []))
        status = pe.get("generation_status", "UNKNOWN")

        dev_status_counts[status] = dev_status_counts.get(status, 0) + 1
        if raw_rank == 1:
            dev_top1 += 1
        if appr_in_ctx:
            dev_appr += 1
        print(f"[{r['question_id']}] PaperRank: {raw_rank}, ApprSurvived: {appr_in_ctx}, Passages: {passages_count}, Status: {status}")

    n_dev = len(dev_records)
    print(f"Dev Raw Paper Rank 1: {dev_top1}/{n_dev} ({dev_top1/n_dev:.4f})")
    print(f"Dev Approved Passage in Context: {dev_appr}/{n_dev} ({dev_appr/n_dev:.4f})")
    print(f"Dev Status Breakdown: {dev_status_counts}")

    print(f"\n=== DISCLOSED PILOT EVALUATION ===")
    if not held:
        print("Disclosed pilot evaluation has not run yet (pending completion of frozen dev run).")
        return
    held_records = held.get("records", [])
    print(f"(N={len(held_records)} across 4 papers)")
    held_top1 = 0
    held_appr = 0
    held_status_counts = {}
    for r in held_records:
        diag = r.get("retrieval_diagnostics") or r.get("retrieval_and_rerank", {})
        boundary = r.get("generation_boundary") or r.get("retrieval_and_rerank", {})
        pe = r.get("pipeline_execution", {})

        raw_rank = diag.get("raw_paper_rank")
        appr_in_ctx = boundary.get("approved_passage_in_final_context") or boundary.get("approved_passage_in_verified_context", False)
        passages_count = boundary.get("verified_context_count") or len(boundary.get("selected_context", []))
        status = pe.get("generation_status", "UNKNOWN")

        held_status_counts[status] = held_status_counts.get(status, 0) + 1
        if raw_rank == 1:
            held_top1 += 1
        if appr_in_ctx:
            held_appr += 1
        print(f"[{r['question_id']}] PaperRank: {raw_rank}, ApprSurvived: {appr_in_ctx}, Passages: {passages_count}, Status: {status}")

    n_held = len(held_records)
    if n_held > 0:
        print(f"Disclosed Pilot Raw Paper Rank 1: {held_top1}/{n_held} ({held_top1/n_held:.4f})")
        print(f"Disclosed Pilot Approved Passage in Context: {held_appr}/{n_held} ({held_appr/n_held:.4f})")
        print(f"Disclosed Pilot Status Breakdown: {held_status_counts}")

if __name__ == "__main__":
    summarize()
