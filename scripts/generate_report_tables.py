"""
Script to parse evaluation results JSON files and generate verified,
code-derived markdown tables for PHASE4_EXECUTION_REPORT_CORRECTED.md
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def generate_tables():
    hybrid_path = ROOT / "evaluation_results/phase4-hybrid.json"
    dense_path = ROOT / "evaluation_results/phase4-dense-only.json"
    bm25_path = ROOT / "evaluation_results/phase4-bm25-only.json"
    rerank_path = ROOT / "evaluation_results/phase4-hybrid-rerank-30-final.json"

    with open(hybrid_path, "r", encoding="utf-8") as f:
        hybrid_data = json.load(f)
    with open(dense_path, "r", encoding="utf-8") as f:
        dense_data = json.load(f)
    with open(bm25_path, "r", encoding="utf-8") as f:
        bm25_data = json.load(f)
    with open(rerank_path, "r", encoding="utf-8") as f:
        rerank_data = json.load(f)

    hybrid_questions = {q["id"]: q for q in hybrid_data["per_question"]["hybrid"]}
    dense_questions = {q["id"]: q for q in dense_data["per_question"]["dense-only"]}
    bm25_questions = {q["id"]: q for q in bm25_data["per_question"]["bm25-only"]}
    rerank_questions = {q["id"]: q for q in rerank_data["per_question"]["hybrid"]}

    qids = [f"Q{i:03d}" for i in range(1, 19)]

    print("### Table 1: Per-Question Retrieval & Rerank Diagnostics (Q001-Q018)\n")
    print("| QID | Target Gold Paper | Physical Pages | Hybrid Rank | Dense Rank | BM25 Rank | Post-Rerank Paper Rank | First Chunk Rank | Appr. Page Rank | Survive Process-K | Survive Adaptive | Distinct Papers (Top 30) | Available Cutoffs |")
    print("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |")

    for qid in qids:
        hq = hybrid_questions[qid]
        dq = dense_questions[qid]
        bq = bm25_questions[qid]
        rq = rerank_questions[qid]

        target = hq["known_sources"][0]
        pages = ", ".join(str(p["page"]) for p in hq["supporting_pages"] if p.get("page"))

        h_rank = hq["known_source_rank"]
        d_rank = dq["known_source_rank"]
        b_rank = bq["known_source_rank"]

        rr_meta = rq["reranker"]
        r_paper_rank = rr_meta["first_distinct_paper_rank"]
        r_chunk_rank = rr_meta["first_chunk_rank"]
        r_appr_rank = rr_meta["first_approved_page_rank"]
        surv_pk = "Yes" if rr_meta["survive_process_k"] else "No"
        surv_ad = "Yes" if rr_meta["survive_adaptive"] else "No"

        distinct_papers = hq["pool"]["distinct_papers"]

        cutoffs = []
        for k in [1, 3, 5, 10]:
            if distinct_papers >= k:
                cutoffs.append(f"K={k}")
        cutoff_str = ", ".join(cutoffs) if cutoffs else "None"

        print(f"| **{qid}** | `{target}` | {pages} | {h_rank} | {d_rank} | {b_rank} | **{r_paper_rank}** | {r_chunk_rank} | {r_appr_rank} | {surv_pk} | {surv_ad} | {distinct_papers} | {cutoff_str} |")

    print("\n\n### Table 2: Aggregate Variant Comparison\n")
    print("| Metric | Hybrid (Control) | Dense-Only | BM25-Only | Hybrid + Frozen 30 Rerank |")
    print("| :--- | :---: | :---: | :---: | :---: |")

    h_agg = hybrid_data["aggregate"]["hybrid"]
    d_agg = dense_data["aggregate"]["dense-only"]
    b_agg = bm25_data["aggregate"]["bm25-only"]
    r_agg = rerank_data["aggregate"]["hybrid"]["reranker_aggregate"]

    print(f"| **Known-Source Hit@1** | {h_agg['cutoffs']['k_1']['known_source_hit_mean']:.4f} ({h_agg['cutoffs']['k_1']['coverage']}/18) | {d_agg['cutoffs']['k_1']['known_source_hit_mean']:.4f} ({d_agg['cutoffs']['k_1']['coverage']}/18) | {b_agg['cutoffs']['k_1']['known_source_hit_mean']:.4f} ({b_agg['cutoffs']['k_1']['coverage']}/18) | **{r_agg['first_distinct_paper_hit_1_count']/r_agg['n']:.4f} ({r_agg['first_distinct_paper_hit_1_count']}/18)** |")

    # Calculate available denominators and hits for reranked pool
    r_per_q = rerank_data["per_question"]["hybrid"]
    r_avail_k3 = sum(1 for q in r_per_q if q["pool"]["distinct_papers"] >= 3)
    r_avail_k5 = sum(1 for q in r_per_q if q["pool"]["distinct_papers"] >= 5)
    r_avail_k10 = sum(1 for q in r_per_q if q["pool"]["distinct_papers"] >= 10)

    r_hit_k3 = sum(1 for q in r_per_q if q["pool"]["distinct_papers"] >= 3 and q["reranker"]["first_distinct_paper_rank"] <= 3)
    r_hit_k5 = sum(1 for q in r_per_q if q["pool"]["distinct_papers"] >= 5 and q["reranker"]["first_distinct_paper_rank"] <= 5)
    r_hit_k10 = sum(1 for q in r_per_q if q["pool"]["distinct_papers"] >= 10 and q["reranker"]["first_distinct_paper_rank"] <= 10)

    def fmt_cell(cd):
        m = cd.get("known_source_hit_mean")
        n = cd.get("n", 0)
        u = cd.get("unavailable", 0)
        if m is None or n == 0:
            return f"n/a (0 avail, {u} unavail)"
        hits = round(m * n)
        return f"{m:.4f} ({hits}/{n} avail, {u} unavail)"

    d3_str = fmt_cell(d_agg['cutoffs']['k_3'])
    b3_str = fmt_cell(b_agg['cutoffs']['k_3'])
    h3_str = fmt_cell(h_agg['cutoffs']['k_3'])
    r3_str = f"**{r_hit_k3/r_avail_k3:.4f} ({r_hit_k3}/{r_avail_k3} avail, {18 - r_avail_k3} unavail)**"
    print(f"| **Known-Source Hit@3** | {h3_str} | {d3_str} | {b3_str} | {r3_str} |")

    d5_str = fmt_cell(d_agg['cutoffs']['k_5'])
    b5_str = fmt_cell(b_agg['cutoffs']['k_5'])
    h5_str = fmt_cell(h_agg['cutoffs']['k_5'])
    r5_str = f"**{r_hit_k5/r_avail_k5:.4f} ({r_hit_k5}/{r_avail_k5} avail, {18 - r_avail_k5} unavail)**"
    print(f"| **Known-Source Hit@5** | {h5_str} | {d5_str} | {b5_str} | {r5_str} |")

    d10_str = fmt_cell(d_agg['cutoffs']['k_10'])
    b10_str = fmt_cell(b_agg['cutoffs']['k_10'])
    h10_str = fmt_cell(h_agg['cutoffs']['k_10'])
    r10_str = f"**{r_hit_k10/r_avail_k10:.4f} ({r_hit_k10}/{r_avail_k10} avail, {18 - r_avail_k10} unavail)**"
    print(f"| **Known-Source Hit@10** | {h10_str} | {d10_str} | {b10_str} | {r10_str} |")

    print(f"| **Known-Source MRR** | {h_agg['mrr_known_positive']['mean']:.4f} | {d_agg['mrr_known_positive']['mean']:.4f} | {b_agg['mrr_known_positive']['mean']:.4f} | **{r_agg['mrr_known_positive_post_rerank']:.4f}** |")

    # Distinct papers average
    h_dist = sum(q["pool"]["distinct_papers"] for q in hybrid_data["per_question"]["hybrid"]) / 18
    d_dist = sum(q["pool"]["distinct_papers"] for q in dense_data["per_question"]["dense-only"]) / 18
    b_dist = sum(q["pool"]["distinct_papers"] for q in bm25_data["per_question"]["bm25-only"]) / 18
    print(f"| **Avg Distinct Papers** | {h_dist:.2f} | {d_dist:.2f} | {b_dist:.2f} | {h_dist:.2f} (evaluated pool) |")

    # Timing
    h_time = sum(q["timing_seconds"] for q in hybrid_data["per_question"]["hybrid"]) / 18
    d_time = sum(q["timing_seconds"] for q in dense_data["per_question"]["dense-only"]) / 18
    b_time = sum(q["timing_seconds"] for q in bm25_data["per_question"]["bm25-only"]) / 18
    r_time = r_agg["mean_timing_seconds"]
    print(f"| **Mean Timing (Seconds)** | {h_time:.2f}s | {d_time:.2f}s | {b_time:.2f}s | {r_time:.2f}s (CPU) |")

if __name__ == "__main__":
    generate_tables()
