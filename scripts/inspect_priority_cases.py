"""
Inspect priority review cases Q001, Q008, Q009, Q011, Q020, Q022 from development generation results.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def inspect_cases():
    dev_path = ROOT / "evaluation_results/phase4_dev_generation_results.json"
    dev = json.loads(dev_path.read_text(encoding="utf-8"))
    priority_ids = {"Q001", "Q008", "Q009", "Q011", "Q020", "Q022"}

    for r in dev["records"]:
        if r["question_id"] in priority_ids:
            qid = r["question_id"]
            gold = r["gold_paper"]
            appr = r["approved_pages"]
            q = r["question"]
            ctx = r["retrieval_and_rerank"]["selected_context"]

            print("=" * 70)
            print(f"{qid} | Target Gold: {gold} | Approved Pages: {appr}")
            print(f"Question: {q}")
            print(f"Selected Context Count: {len(ctx)}")
            for i, c in enumerate(ctx, 1):
                src = c["source_filename"]
                pg = c["page"]
                cid = c["chunk_id"]
                txt = " ".join(c["exact_text_passed_to_generation"].split())
                print(f"  [{i}] Source: {src} | Physical Page: {pg} | Chunk ID: {cid}")
                print(f"      Passage: {txt[:220]}...")

if __name__ == "__main__":
    inspect_cases()
