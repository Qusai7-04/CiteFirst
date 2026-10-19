"""Evidence-gated document retrieval evaluation before CRAG reranking/generation."""
import argparse
import csv
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

from evaluation.dataset import audit_records, load_dataset
from evaluation.metrics import KS, macro_average, score_ranking
from settings_config import load_settings

ROOT = Path(__file__).resolve().parent
CHUNK_CANDIDATE_LIMIT = 10


def evaluate_dataset(records, dataset_hash, retriever=None, limit=None, audit_only=False,
                     index_tag="unrecorded", code_commit="unknown", config_sha256="unrecorded"):
    if limit is not None and (type(limit) is not int or limit < 1):
        raise ValueError("--limit must be a positive integer")
    audit = audit_records(records)
    output, attempted = [], 0
    for record, row in zip(records, audit):
        result = {key: value for key, value in row.items()
                  if key not in ("evidence", "judged_nonrelevant_papers")}
        result.update(dataset_sha256=dataset_hash, index_tag=index_tag, code_commit=code_commit,
                      config_sha256=config_sha256,
                      retrieved_papers=[], retrieved_chunks=[], metrics={}, error=None,
                      chunk_candidates_returned=0, distinct_papers_returned=0,
                      gold_evidence_refs=[
                          {"source_filename": item.get("source_filename"), "page": item.get("page")}
                          for item in row["evidence"] if isinstance(item, dict)])
        if row["status"] == "eligible_abstention":
            result["status"] = "skipped_unanswerable"
        elif row["status"] == "eligible_retrieval":
            if audit_only:
                result["status"] = "skipped_audit_only"
            elif limit is not None and attempted >= limit:
                result["status"] = "skipped_limit"
            else:
                attempted += 1
                try:
                    if retriever is None:
                        from database import search_vault
                        retriever = search_vault
                    raw = retriever(record["question"], n_results=CHUNK_CANDIDATE_LIMIT)
                    # shortcut: score only the first ten returned chunks; increase the
                    # candidate window before claiming top-ten coverage of unique papers.
                    metas = raw["metadatas"][0][:CHUNK_CANDIDATE_LIMIT]
                    if not all(isinstance(meta, dict) and meta.get("source") for meta in metas):
                        raise ValueError("missing_source_metadata")
                    result["retrieved_chunks"] = [
                        {"rank": rank, "source_filename": meta["source"],
                         "chunk_id": meta.get("chunk_id"),
                         "page": (meta["page_index"] + 1
                                  if type(meta.get("page_index")) is int else None),
                         "score": None}
                        for rank, meta in enumerate(metas, 1)]
                    ranked = list(dict.fromkeys(meta["source"] for meta in metas))[:CHUNK_CANDIDATE_LIMIT]
                    result["chunk_candidates_returned"] = len(metas)
                    result["distinct_papers_returned"] = len(ranked)
                    result["retrieved_papers"] = [
                        {"rank": rank, "source_filename": name, "score": None}
                        for rank, name in enumerate(ranked, 1)]
                    grades = None
                    if all(item.get("relevance_grade") is not None for item in row["evidence"]):
                        grades = {}
                        for item in row["evidence"]:
                            name = item["source_filename"]
                            grades[name] = max(grades.get(name, 0), item["relevance_grade"])
                    judged = set(row["gold_papers"]) | set(row["judged_nonrelevant_papers"])
                    result["metrics"] = score_ranking(
                        ranked, row["gold_papers"], grades=grades, judged_ids=judged)
                    result["status"] = "scored"
                except Exception as exc:
                    result["status"] = "failed"
                    result["error"] = f"{type(exc).__name__}: {exc}"
        output.append(result)
    counts = Counter(row["status"] for row in output)
    summary = {
        "dataset_sha256": dataset_hash, "index_tag": index_tag, "code_commit": code_commit,
        "config_sha256": config_sha256,
        "config": {"retrieval": "database.search_vault",
                   "chunk_candidate_limit": CHUNK_CANDIDATE_LIMIT,
                   "paper_ranking": "first occurrence among top ten returned chunks",
                   "k": list(KS), "limit": limit, "level": "source_filename",
                   "mode": "hybrid_pre_crag_no_llm"},
        "counts": {"present": len(records), "valid": sum(r["status"] != "invalid" for r in audit),
                   "eligible_retrieval": sum(r["status"] == "eligible_retrieval" for r in audit),
                   "eligible_abstention": sum(r["status"] == "eligible_abstention" for r in audit),
                   "excluded": sum(r["status"] in ("invalid", "needs_human_review") for r in audit),
                   "attempted": attempted, "scored": counts["scored"],
                   "failed": counts["failed"], "skipped": counts["skipped_limit"] +
                   counts["skipped_unanswerable"] + counts["skipped_audit_only"]},
        "metrics": macro_average(row["metrics"] for row in output if row["status"] == "scored"),
        "baseline_status": ("not_run_audit_only" if audit_only else
                            "blocked_no_verified_labels" if not any(
                                r["status"] == "eligible_retrieval" for r in audit) else
                            "retrieval_failed" if not counts["scored"] else
                            "partial_results" if counts["failed"] else "pilot_only"),
    }
    return audit, output, summary


def write_reports(output_dir, audit, results, summary):
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "annotation-gaps.csv").open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["id", "position", "status", "reasons",
                                                  "evidence_status", "possible_correction",
                                                  "needs_human_review"])
        writer.writeheader()
        for row in audit:
            writer.writerow({"id": row["id"], "position": row["position"],
                             "status": row["status"], "reasons": ";".join(row["reasons"]),
                             "evidence_status": "verified_recorded" if row["status"] == "eligible_retrieval"
                             else "not_verified",
                             "possible_correction": "Check original PDF; annotate source, page, quote and answer",
                             "needs_human_review": row["status"] != "eligible_retrieval"})
    with (directory / "per-question.jsonl").open("w", encoding="utf-8") as file:
        for row in results:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")
    (directory / "aggregate.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Retrieval evaluation", "",
        f"Status: **{summary['baseline_status']}**; document-level hybrid search before CRAG.",
        f"Dataset SHA-256: {summary['dataset_sha256']}; index tag: {summary['index_tag']}; "
        f"code commit: {summary['code_commit']}.", "",
        "Counts: " + ", ".join(f"{key}={value}" for key, value in summary["counts"].items()) + ".",
        f"Config: {json.dumps(summary['config'], sort_keys=True)}", "",
        "Paper ranks are first occurrences within the top ten returned chunks. "
        "Fewer than K distinct papers are padded as misses; this is not a search "
        "over the top K unique papers.", "",
        "Macro means across scored answerable queries (missing ranks count as non-relevant):", "",
    ]
    if summary["metrics"]:
        lines += ["| Metric | Mean | N |", "|---|---:|---:|"]
        lines += [f"| {key} | {value['mean']:.4f} | {value['count']} |"
                  for key, value in summary["metrics"].items()]
    else:
        lines += ["No verified relevance labels; no retrieval quality score is reportable."]
    lines += ["", "Unanswerable questions and failed queries are excluded from means. "
              "Answer, citation, faithfulness and abstention require separate human review.", ""]
    (directory / "report.md").write_text("\n".join(lines), encoding="utf-8")


def run_ml_evaluation(dataset=ROOT / "golden_dataset.json",
                      output_dir=ROOT / "evaluation_results", limit=None,
                      audit_only=False, index_tag=None, code_commit=None):
    records, digest = load_dataset(dataset)
    if (not audit_only and any(row["status"] == "eligible_retrieval"
                           for row in audit_records(records)) and
            (not isinstance(index_tag, str) or not index_tag.strip()
             or index_tag.strip().lower() in {"unrecorded", "unknown"})):
        raise ValueError("A fixed --index-tag is required for a scored retrieval run")
    if code_commit is None:
        process = subprocess.run(["git", "rev-parse", "--verify", "HEAD"], cwd=ROOT,
                                 capture_output=True, text=True, check=False)
        code_commit = process.stdout.strip() if process.returncode == 0 else "unknown"
    settings = load_settings()
    config_sha256 = hashlib.sha256(
        json.dumps(settings, sort_keys=True).encode("utf-8")).hexdigest()
    audit, rows, summary = evaluate_dataset(
        records, digest, limit=limit, audit_only=audit_only,
        index_tag=index_tag, code_commit=code_commit, config_sha256=config_sha256)
    write_reports(output_dir, audit, rows, summary)
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=ROOT / "golden_dataset.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "evaluation_results")
    parser.add_argument("--limit", type=int, help="Explicit cap on eligible answerable queries")
    parser.add_argument("--audit-only", action="store_true")
    parser.add_argument("--index-tag", help="Required for a scored retrieval run; identify the fixed local index")
    parser.add_argument("--code-commit")
    args = parser.parse_args()
    print(json.dumps(run_ml_evaluation(**vars(args)), indent=2))
