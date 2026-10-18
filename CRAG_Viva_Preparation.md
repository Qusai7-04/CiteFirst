# CRAG Intelligence Platform - Viva Preparation Guide

This guide is designed to help you confidently present and defend your Corrective Retrieval-Augmented Generation (CRAG) project to your Machine Learning professor. It breaks down the complete architecture, focusing heavily on the backend, data processing, and ML algorithms.

---

## 1. Project Overview & Goal
**What is this project?**
It is a Full-Stack AI document intelligence platform (CRAG - Corrective Retrieval-Augmented Generation). 
**Goal:** To build an academic-grade QA system that prioritizes **Precision** (eliminating hallucinations/false positives) over wild guessing. It verifies facts before generating an answer.

**Tech Stack summary:**
*   **Backend:** Python, FastAPI, ChromaDB (Vector Database)
*   **Machine Learning / AI:** 
    *   Embeddings: `BAAI/bge-small-en-v1.5`
    *   Reranker: `BAAI/bge-reranker-base` (Cross-Encoder)
    *   LLM Inference: `llama-3.3-70b-versatile` (via Groq for ultra-fast generation)
    *   Evaluator LLM: `llama-3.1-8b-instant`
*   **Frontend:** Next.js 16, React 19, TailwindCSS

---

## 2. Dataset & Ground Truth
**What dataset is used?**
*   **Raw Data:** The system operates on a vault of **66 academic PDF papers** (located in the `papers/` directory). These range across various domains (Computer Networks, Machine Learning, Signal Processing, Biology, Physics).
*   **Golden Dataset (`golden_dataset.json`):** You generated a test dataset of 100 complex Question-Answer pairs using **DeepSeek-R1** (via OpenRouter). DeepSeek read the chunks and formulated complex reasoning questions and accurate ground-truth answers. This file is used specifically for evaluating the system's performance.

---

## 3. Data Processing & Chunking Strategy (Crucial)
*If the professor asks: "How do you split your documents?"*

You use an advanced **Parent-Child (Two-Tier) Chunking Strategy**.
1.  **Child Chunks (100 words, 20 overlap):** These smaller chunks are converted into vector embeddings. Why? Because small chunks capture very highly concentrated semantic meaning, making dense search highly accurate. 
2.  **Parent Chunks (350 words, 75 overlap):** These are larger sections encompassing the child chunks. They are stored in the database by ID (not embedded). 

**How it ties together during search:**
When the user asks a question, the system searches against the *Child Chunks*. If a child chunk is heavily relevant, the system doesn't just feed the 100 words to the LLM; it retrieves the **Parent Chunk** using a `parent_id` link. This gives the final LLM much broader context while maintaining the precision of small-chunk searching. 

---

## 4. The Backend: 4-Phase Logic Engine Step-by-Step
This is the core of your project (`logic_engine.py` and `database.py`). It prevents hallucinations.

### Phase 1: Hybrid Mathematical Retrieval (`database.py`)
1.  **Intent Routing:** The query is routed to a specific domain (e.g., matching keywords to "computer_vision" or "quantum") to optionally filter results.
2.  **Hybrid Search:**
    *   **Dense Search:** The query is embedded (using `bge-small`) and matched via Cosine Distance against ChromaDB.
    *   **Sparse Search (BM25):** The query undergoes keyword-based matching to catch exact terminology.
3.  **Reciprocal Rank Fusion (RRF):** The results from Dense and Sparse searches are mathematically fused to retrieve the Top 30 candidates.
4.  **Parent Expansion:** The highly relevant child chunks are expanded into their 350-word parent chunks.

### Phase 2: Tri-State Logic Engine & Reranking (`logic_engine.py`)
1.  **Cross-Encoder Grading:** The top chunks are evaluated one-by-one against the query using `bge-reranker-base`. A cross-encoder reads the *(query, chunk)* together, outputting a highly accurate relevance logit score (converted via Sigmoid).
2.  **Adaptive Softmax:** A gentle filter scrubs out extreme "tail noise" (retaining 90% of the probability mass).
3.  **Tri-State Routing:** 
    *   **CORRECT (Score ≥ 0.55):** Instantly passed to the verified context array.
    *   **AMBIGUOUS (0.25 ≤ Score < 0.55):** An LLM attempts to rescue a specific factual sentence from the chunk. If the sentence is useful, a *supplemental sub-query* is executed to find missing puzzle pieces.
    *   **INCORRECT (Score < 0.25):** Dropped to prevent hallucinations.
4.  **Hard Cap:** Only the absolute best 2 chunks (`MAX_VERIFIED_CHUNKS`) survive.

### Phase 3: Pre-Flight Combined Relevance Check (The FP Killer)
*This is your unique architectural innovation to drop False Positives (FPs).*
1.  The remaining verified chunks are grouped together.
2.  Before generating the final answer, an LLM acts as a strict judge: *"Does this combined context directly and completely answer the query?"*
3.  If **YES**, proceed to generate. If **NO**, the system intercepts the bad context, throws it out, and moves to Phase 4.

### Phase 4: Adaptive Fallback & Controlled Generation
1.  **Fallback (Rewrite):** If Phase 3 failed, an LLM rewrites the user's query using better scientific vocabulary and tries the pipeline again.
2.  **Bendy Mode:** If the second attempt fails to perfectly match, the system grabs partially relevant chunks (`BENDY_THRESHOLD >= 0.10`) and generates a "Soft Answer" (explicitly stating: "I couldn't find a direct answer, but here is related info...").
3.  **Final Generation:** The `llama-3.3-70b-versatile` model looks strictly at the verified context and generates a structured answer, citing its sources.

---

## 5. Evaluation & Achievements
**How is it tested (`evaluator.py`)?**
*   The system automates testing by looping through your `golden_dataset.json`.
*   An LLM Judge (`llama-3.1-8b-instant`) reads the Ground Truth, the Pipeline's Fact output, and grades it True/False.
*   **Metrics Calculated:** True Positives (TP), False Positives (FP), FN, TN. Resulting in **Precision, Recall, F1-Score, and Accuracy.**

**What was achieved?**
*   By implementing Phase 3 (Pre-flight check), you stopped the system from injecting False Positives. If context isn't perfect, it blocks it (returning empty arrays) rather than returning 2 wrong chunks. This effectively raises **Precision** dramatically.
*   By using the Parent-Child chunking, the model retained massive context recall while shrinking embedding latency.

---

## 6. Likely Questions Your Professor Will Ask

**Q1: Why did you use a Cross-Encoder (bge-reranker) instead of just relying on Cosine Similarity (ChromaDB)?**
> **A:** "Cosine similarity using Bi-Encoders is fast but misses deep semantic nuance because the query and document are embedded separately. A Cross-Encoder feeds both the query and document into the transformer simultaneously. This allows the self-attention mechanism to compare words directly between the query and the chunk, yielding vastly superior accuracy when reranking."

**Q2: What happens if a user asks a question that is NOT in the PDFs?**
> **A:** "Because of Phase 2's Tri-State Reranking, irrelevant chunks fail to cross the `CORRECT_THRESHOLD` (0.55). Furthermore, Phase 3 strictly evaluates the combined chunks. The system will politely respond: 'No information detected from the papers for your query' rather than hallucinating an answer."

**Q3: Why Groq?**
> **A:** "Groq utilizes LPU (Language Processing Unit) inference technology, which provides incredibly high token-per-second output. Because my pipeline requires multiple LLM calls (grading, rewriting, combined check, final answer), standard APIs would be too slow. Groq allows all 4 phases to execute within streamable real-time limits."

**Q4: How did you evaluate the performance of your RAG?**
> **A:** "I used LLM-as-a-Judge. I created a golden dataset comprising 100 reasoning questions and ground truths. My evaluator script asks the pipeline the questions, monitors the retrieved chunks, and asks a strict model (Llama 3.1 8b) to judge whether the retrieved factual context contains the ground truth. This allowed me to rigorously calculate Precision, Recall, and F1 scores programmatically."

**Q5: What is the purpose of the 'Ambiguous' state in the Logic Engine?**
> **A:** "If a chunk's relevance is borderline (e.g., 0.35), it usually means it contains one good sentence buried in irrelevant noise. The Ambiguous flow extracts *just* that good sentence, and then generates a 'supplemental sub-query' in the background to fetch missing supporting evidence from the vector database before deciding if it should be kept."
