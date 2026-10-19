# Human annotation worksheet

Check the original PDF, not the generated contexts. Preserve the checked-in 18 candidate questions and generated answers; use a separate reviewed JSON dataset with the same fields plus explicit annotations. The audit's positional legacy-001 through legacy-018 IDs identify only the exact file SHA-256 in phase3-audit.md. Preserve order and file hash while assigning permanent IDs.

Illustrative record structure only; no values here are real gold labels:

    {
      "id": "Q001",
      "question": "<existing candidate question>",
      "ground_truth": "<existing generated, unverified answer>",
      "contexts": ["<existing input excerpt>"],
      "answerable": true,
      "reference_answer": "<human-approved answer>",
      "required_claims": ["<human-approved claim>"],
      "question_type": "method",
      "split": "development",
      "human_verified": true,
      "relevant_evidence": [
        {"source_filename": "<exact indexed PDF name>.pdf",
         "page": 1, "supporting_quote": "<exact checked PDF excerpt>",
         "relevance_grade": 2}
      ],
      "judged_nonrelevant_papers": []
    }

Do not append the example to the benchmark. Grade is optional for binary labels: 1 partially useful, 2 directly supporting, 3 essential/complete. A paper with multiple spans takes its highest verified grade for document NDCG. Page is one-based PDF page, not printed pagination. Multi-hop questions need every supporting passage. Source filename is the exact index metadata source; chunk IDs are derived and unstable. Review the candidate answer for unsupported inferences, maintain the reviewed reference separately, note reviewer/date in annotation records, check duplicates, and set human_verified true only after verification. Unverified candidates remain false with reasons.

For reviewed unanswerable items: answerable false, question_type unanswerable, corpus_reviewed true, relevant_evidence empty. A retriever miss is insufficient; inspect the fixed full corpus. Add explicitly judged irrelevant retrieved filenames in judged_nonrelevant_papers; leave uncertain ones unjudged. Re-run python evaluator.py --audit-only --dataset reviewed_dataset.json before a baseline.

After the pilot, pragmatically target 120–180 human-verified questions across roughly 60 papers, about 2–3 per paper on average. Cover factual, method, result, limitation, comparison, multi-hop, and reviewed unanswerable items. Track paper/topic/type coverage. Group near duplicates and questions from the same passage into one split; iterate on development and reserve a sufficiently sized held-out test. Report counts and coverage by split; this 18-item pilot is not a stable final test.
