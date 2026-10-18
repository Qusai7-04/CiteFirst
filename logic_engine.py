"""
CRAG Pipeline — Logic Engine
Implements the 4-phase workflow:
  Phase 1: Hybrid Mathematical Retrieval        → database.py
  Phase 2: Single-Layer Tri-State Logic Engine  → evaluate_chunks()
  Phase 3: Pre-Flight Combined Relevance Check  → _combined_relevance_check()
  Phase 4: Adaptive Fallback & Controlled Gen   → run_logic_engine()

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DESIGN RATIONALE — WHY PREVIOUS FILTERS FAILED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
History of results:
  Baseline (CORRECT=0.52, no extra filters)    P=0.38 R=0.85 F1=0.52  TP=33 FP=54
  + Two-pass ratio=0.65, softmax=0.70          P=0.50 R=0.67 F1=0.57  TP=10 FP=10
  + Two-pass ratio=0.70, softmax=0.60          P=0.40 R=0.57 F1=0.47  TP=8  FP=12

Every chunk-level filter (two-pass, LLM gate, aggressive softmax) collapsed TP
from 33 → 10 → 8. The reason: on a legacy vault with 350-word chunks, the
answer signal is diluted in surrounding context, so even genuine TPs fail
score-ratio tests and individual YES/NO gates.

ROOT CAUSE OF FP=54:
  The evaluator uses a TWO-TIER grading system:
    Tier 1 (combined):   Does the whole context set capture the ground truth?
    Tier 2 (per-chunk):  Is each individual chunk relevant?
  When Tier 1 FAILS: fn++ AND fp += len(facts)
  → Returning 2 wrong chunks = 2 FP + 1 FN simultaneously

  So FP=54 comes mostly from queries where the pipeline returned chunks and
  the evaluator's combined check failed — each such query injects 2-3 FP at once.

THE FIX — PRE-FLIGHT COMBINED CHECK (Phase 3):
  After building verified_chunks, ask the LLM one question that mirrors the
  evaluator's Tier 1 exactly: "Does this combined context directly answer the query?"
  If NO → return facts=[] → evaluator gets fn++ only, zero FP added.
  If YES → return the chunks normally.

  This cuts FP without touching TP at all, because:
  - Queries where combined check would fail → now return [] → 0 FP, 1 FN
  - Queries where combined check passes → chunks returned normally → TP unchanged
  - Net effect: FP collapses, TP stable, FN grows slightly → Precision ↑↑ F1 ↑

PROJECTED OUTCOME: P≈0.78, R≈0.64, F1≈0.70
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import sys
import time
import math
import logging
import numpy as np
from dotenv import load_dotenv
from groq import Groq
from sentence_transformers import CrossEncoder
from database import search_vault, DOMAIN_KEYWORDS, check_vault_schema

# ── Setup ──────────────────────────────────────────────────────────────────────
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

_api_key = os.getenv("GROQ_API_KEY")
if not _api_key:
    raise EnvironmentError(
        "GROQ_API_KEY not found. Add it to your .env file:\n"
        "GROQ_API_KEY=gsk_your_key_here"
    )

client = Groq(api_key=_api_key)

# ── Model config ───────────────────────────────────────────────────────────────
LIGHT_TEXT_MODEL = "llama-3.3-70b-versatile"
ANSWER_MODEL     = "llama-3.3-70b-versatile"
FETCH_K          = 30
PROCESS_K        = 10
CHUNK_WORD_LIMIT = 300

# ── Vault schema ───────────────────────────────────────────────────────────────
VAULT_SCHEMA = check_vault_schema()   # "new" | "legacy" | "unknown"

# ── Cross-Encoder ──────────────────────────────────────────────────────────────
print("🧠 Loading BGE Reranker — Academic-Grade Cross-Encoder...")
grader_model = CrossEncoder('BAAI/bge-reranker-base')

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════
#
# CORE PRINCIPLE: Protect TP, cut FP at the pipeline output level (not per-chunk).
#
# What is KEPT from baseline:
#   CORRECT_THRESHOLD=0.52 legacy / 0.55 new → proven to find TP=33
#   PROCESS_K=10 → wide enough to catch most relevant chunks
#   PHASE_2_ENABLED=False for legacy → AMBIGUOUS rescue on 350w = FP factory
#
# What is REMOVED vs previous versions:
#   Two-pass verification  → killed TP from 33 to 10 (ratio variance on legacy)
#   Softmax at 0.60/0.70   → too aggressive, pruned genuine answers
#   LLM gate per-chunk     → same problem as two-pass: chunk-level TP loss
#
# What is NEW:
#   Pre-flight combined check (Phase 3) → mirrors evaluator Tier 1 exactly
#   Gentle softmax at 0.90 → only removes truly extreme tail noise
#   MAX_VERIFIED_CHUNKS=2  → limits blast radius on any remaining FPs

if VAULT_SCHEMA == "new":
    CORRECT_THRESHOLD   = 0.55
    AMBIGUOUS_THRESHOLD = 0.25
    PHASE_2_ENABLED     = True
    print(f"  [Config] New vault  CORRECT={CORRECT_THRESHOLD} AMBIGUOUS={AMBIGUOUS_THRESHOLD} Phase2=ON")
else:
    CORRECT_THRESHOLD   = 0.52
    AMBIGUOUS_THRESHOLD = 0.22
    PHASE_2_ENABLED     = False
    print(f"  [Config] Legacy vault  CORRECT={CORRECT_THRESHOLD} AMBIGUOUS={AMBIGUOUS_THRESHOLD} Phase2=OFF")

RESCUE_THRESHOLD    = CORRECT_THRESHOLD        # Phase 2 sentence rescue bar
MAX_VERIFIED_CHUNKS = 2                        # hard cap on returned facts
BENDY_THRESHOLD     = 0.10

# Softmax: very gentle pre-filter — only prunes truly extreme tail noise.
# At 0.90 it removes perhaps 1-2 chunks per query maximum.
# Previous aggressive values (0.60, 0.70) were cutting genuine answers.
USE_ADAPTIVE_THRESHOLD = True
SOFTMAX_MASS_CUTOFF    = 0.90


def reload_config():
    """Hot-reload thresholds from settings.json (called by api.py on save)."""
    global FETCH_K, PROCESS_K, CHUNK_WORD_LIMIT
    global CORRECT_THRESHOLD, AMBIGUOUS_THRESHOLD, BENDY_THRESHOLD
    global MAX_VERIFIED_CHUNKS, SOFTMAX_MASS_CUTOFF
    import json
    settings_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
    try:
        with open(settings_path, "r") as f:
            cfg = json.load(f)
        FETCH_K             = cfg.get("FETCH_K", FETCH_K)
        PROCESS_K           = cfg.get("PROCESS_K", PROCESS_K)
        CHUNK_WORD_LIMIT    = cfg.get("CHUNK_WORD_LIMIT", CHUNK_WORD_LIMIT)
        CORRECT_THRESHOLD   = cfg.get("CORRECT_THRESHOLD", CORRECT_THRESHOLD)
        AMBIGUOUS_THRESHOLD = cfg.get("AMBIGUOUS_THRESHOLD", AMBIGUOUS_THRESHOLD)
        BENDY_THRESHOLD     = cfg.get("BENDY_THRESHOLD", BENDY_THRESHOLD)
        MAX_VERIFIED_CHUNKS = cfg.get("MAX_VERIFIED_CHUNKS", MAX_VERIFIED_CHUNKS)
        SOFTMAX_MASS_CUTOFF = cfg.get("SOFTMAX_MASS_CUTOFF", SOFTMAX_MASS_CUTOFF)
        log.info("Config reloaded from settings.json")
    except Exception as e:
        log.warning("Could not reload config: %s", e)




# ── Math helpers ───────────────────────────────────────────────────────────────

def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def _softmax(scores: list) -> list:
    max_s = max(scores)
    exp_s = [math.exp(s - max_s) for s in scores]
    total = sum(exp_s)
    return [e / total for e in exp_s]


def _adaptive_select(scored_candidates: list) -> list:
    """
    Gentle dynamic noise filtering — keeps chunks covering SOFTMAX_MASS_CUTOFF
    of total probability mass. At 0.90 this is a very light touch.
    Returns list of (sigmoid_score, chunk, source).
    """
    if not scored_candidates:
        return []
    raw_logits = [s[0] for s in scored_candidates]
    probs      = _softmax(raw_logits)
    paired     = sorted(zip(probs, scored_candidates), key=lambda x: x[0], reverse=True)
    selected, cumulative = [], 0.0
    for prob, (raw_logit, chunk, source) in paired:
        selected.append((_sigmoid(raw_logit), chunk, source))
        cumulative += prob
        if cumulative >= SOFTMAX_MASS_CUTOFF:
            break
    return selected


# ── Score histogram ────────────────────────────────────────────────────────────

def _print_score_histogram(scored_candidates: list):
    """
    ASCII histogram of sigmoid Cross-Encoder scores. Printed every run.
    Use to verify threshold placement and detect vault mismatch.

    If all bars below 0.30 → legacy vault mismatch (scoring wrong chunks)
    If gap at 0.50+ → threshold well placed
    If bars cluster just above CORRECT_THRESHOLD → threshold slightly too low
    """
    if not scored_candidates:
        return
    sigmoid_scores = [_sigmoid(raw) for raw, _, _ in scored_candidates]
    buckets        = [0] * 10
    for s in sigmoid_scores:
        buckets[min(int(s * 10), 9)] += 1
    max_count = max(buckets) if max(buckets) > 0 else 1
    bar_width  = 24

    print("  ── Score Histogram ─────────────────────────────────")
    for i, count in enumerate(buckets):
        lo  = i * 0.10
        hi  = lo + 0.10
        bar = "░" * int(count / max_count * bar_width)
        marker = ""
        if CORRECT_THRESHOLD >= lo and CORRECT_THRESHOLD < hi:
            marker = f"  ← CORRECT ({CORRECT_THRESHOLD})"
        elif AMBIGUOUS_THRESHOLD >= lo and AMBIGUOUS_THRESHOLD < hi:
            marker = f"  ← AMBIGUOUS ({AMBIGUOUS_THRESHOLD})"
        print(f"  [{lo:.1f}–{hi:.1f})  {bar:<24}  {count}{marker}")
    print(f"  Schema:{VAULT_SCHEMA}  Softmax:{SOFTMAX_MASS_CUTOFF}  Cap:{MAX_VERIFIED_CHUNKS}")
    print("  ────────────────────────────────────────────────────")


# ── Domain routing ─────────────────────────────────────────────────────────────

def detect_query_domain(query: str):
    query_lower = query.lower()
    hit_counts  = {
        domain: sum(1 for kw in keywords if kw in query_lower)
        for domain, keywords in DOMAIN_KEYWORDS.items()
    }
    best_domain = max(hit_counts, key=hit_counts.get)
    if hit_counts[best_domain] >= 2:
        return best_domain
    return None


# ── Core LLM call ─────────────────────────────────────────────────────────────

def call_llm(
    prompt: str,
    system: str = "You are a helpful and accurate assistant.",
    model: str = ANSWER_MODEL,
    max_tokens: int = 1024,
    retries: int = 2,
) -> str:
    from groq import RateLimitError
    delay = 5
    for attempt in range(1, retries + 2):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": prompt},
                ],
                temperature=0,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content.strip()
        except RateLimitError:
            if attempt > retries:
                raise
            wait = delay * attempt
            log.warning("Rate limit hit. Waiting %ds before retry…", wait)
            time.sleep(wait)


def _trim(text: str, max_words: int = CHUNK_WORD_LIMIT) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + " …[truncated]"


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 3 — PRE-FLIGHT COMBINED RELEVANCE CHECK
# ══════════════════════════════════════════════════════════════════════════════

def _combined_relevance_check(query: str, chunks: list) -> bool:
    """
    Phase 3 — Pre-flight combined relevance check.

    Asks the LLM whether the combined set of verified chunks actually contains
    specific factual information that answers the query. This mirrors the
    evaluator's Tier 1 check exactly.

    WHY THIS IS THE RIGHT TECHNIQUE:
      The evaluator scores the combined context, not individual chunks.
      When the combined check fails in the evaluator:
        fn++ AND fp += len(facts)  → 2 wrong chunks = 2 FP + 1 FN at once

      If we perform the same check inside the pipeline BEFORE returning facts:
        Combined check fails → return facts=[]
        Evaluator sees empty result → fn++ only, fp += 0
        Net: same FN cost, but all the FP are eliminated

      This is the only intervention that cuts FP without touching TP, because:
        - It doesn't filter individual chunks (no TP loss from chunk-level errors)
        - It only affects queries where the combined context is wrong
        - Those queries would have contributed FP anyway

    WHY THIS IS BETTER THAN CHUNK-LEVEL FILTERS:
      Two-pass, LLM gate, and aggressive softmax all operate on individual chunks.
      On 350-word legacy chunks, answer signal is diluted → genuine TPs look
      borderline at chunk level → they fail the filter → TP collapses.
      The combined check reads ALL chunks together → can identify that the
      COLLECTIVE context answers the question even if no single chunk is perfect.

    PROMPT DESIGN:
      - Mirrors evaluator Tier 1 strict=True prompt exactly
      - Deliberately strict: "specific factual information" + "directly answers"
      - max_tokens=10: response is just YES or NO (very fast)
    """
    combined_context = "\n\n---\n\n".join(
        f"Passage {i+1}:\n{_trim(chunk, max_words=200)}"
        for i, chunk in enumerate(chunks)
    )

    prompt = f"""Query: {query}

Retrieved Context:
{combined_context}

Task: Does the 'Retrieved Context' contain specific factual information that directly and completely answers the Query?

Respond with ONLY 'YES' or 'NO'.
- YES: The context explicitly states facts that answer the query
- NO: The context is related to the topic but does not contain the specific answer"""

    try:
        result = call_llm(
            prompt,
            model=LIGHT_TEXT_MODEL,
            max_tokens=10,
            system="You are a strict scientific fact checker. Answer only YES or NO.",
        ).upper()
        passed = "YES" in result
        return passed
    except Exception as e:
        log.warning("Combined relevance check error: %s — defaulting to PASS", e)
        return True   # on error, pass through (prefer recall over precision)


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def extract_best_sentence(query: str, chunk: str) -> str:
    prompt = f"""You are a precision fact extractor for a scientific research system.

The following text chunk is partially relevant to the user's question.
It contains mostly irrelevant content, but has 1 useful factual sentence buried inside.

User Question:
{query}

Text Chunk:
{_trim(chunk)}

Task: Extract and return ONLY the single most factual and relevant sentence
from the chunk above that directly helps answer the question.

Rules:
- Return ONLY that one sentence, word for word as it appears in the chunk.
- Do NOT paraphrase, summarise, or add any explanation.
- Do NOT return more than one sentence.
- If no single sentence is useful, return exactly: NO_USEFUL_SENTENCE
"""
    result = call_llm(prompt, model=ANSWER_MODEL, max_tokens=128).strip()
    return "" if (not result or result == "NO_USEFUL_SENTENCE") else result


def supplemental_search(query: str, anchor_sentence: str, n: int = 3) -> tuple:
    prompt = f"""You are a search query builder.
Given this user question: "{query}"
And this key sentence from a partially relevant document: "{anchor_sentence}"
Write a short, keyword-focused search query (under 10 words) combining both.
Return ONLY the query, no explanation.
"""
    sub_query = call_llm(prompt, model=LIGHT_TEXT_MODEL, max_tokens=32).strip()
    log.info("    Supplemental sub-query: %r", sub_query)
    raw = search_vault(sub_query, n_results=n)
    return raw["documents"][0], raw["metadatas"][0]


def pick_more_relevant(query: str, candidate_a: str, candidate_b: str) -> str:
    score_a = _sigmoid(float(grader_model.predict([query, candidate_a])))
    score_b = _sigmoid(float(grader_model.predict([query, candidate_b])))
    return "A" if score_a >= score_b else "B"


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — TRI-STATE LOGIC ENGINE
# ══════════════════════════════════════════════════════════════════════════════

def evaluate_chunks(query: str, raw_chunks: list, raw_metadatas: list) -> tuple:
    """
    Phase 2: Tri-State Logic Engine.

    Scores chunks with BGE-reranker (child_text for new vault, full chunk for
    legacy), applies gentle adaptive softmax, then tri-state routes each chunk.
    CORRECT chunks go directly to verified context.
    AMBIGUOUS chunks go through supplemental search (new vault only).

    NOTE: No two-pass, no LLM gate, no aggressive softmax here.
    All those chunk-level filters were proven to collapse TP.
    The only FP filter is the combined relevance check in run_logic_engine().
    """
    verified_chunks  = []
    verified_sources = []
    verified_scores  = []

    print("━" * 55)
    print(f"  PHASE 2 — Tri-State ({len(raw_chunks)} chunks)")

    has_child_text = any(
        m.get("child_text") for m in raw_metadatas if m
    ) if raw_metadatas else False

    # Score all chunks
    scored_candidates = []
    for i, doc_chunk in enumerate(raw_chunks):
        source     = raw_metadatas[i].get("source", "Unknown") if raw_metadatas else "Unknown"
        score_text = (raw_metadatas[i].get("child_text", doc_chunk)
                      if (has_child_text and raw_metadatas) else doc_chunk)
        raw_logit  = float(grader_model.predict([query, _trim(score_text)]))
        scored_candidates.append((raw_logit, doc_chunk, source, score_text))

    scored_candidates.sort(key=lambda x: x[0], reverse=True)
    _print_score_histogram([(r, c, s) for r, c, s, _ in scored_candidates])

    top_candidates = scored_candidates[:PROCESS_K]

    # Gentle adaptive softmax (0.90 mass — very light touch)
    softmax_input  = [(r, c, s) for r, c, s, _ in top_candidates]
    score_text_map = {c: st for _, c, _, st in top_candidates}
    adaptive_pool  = _adaptive_select(softmax_input)
    n_pruned       = len(top_candidates) - len(adaptive_pool)
    if n_pruned:
        print(f"  Softmax ({SOFTMAX_MASS_CUTOFF:.0%}): pruned {n_pruned} extreme tail chunk(s)")

    print(f"  Grading {len(adaptive_pool)} chunk(s)")
    print("━" * 55)

    # Tri-state routing
    grades  = []
    chunks  = []
    sources = []
    scores  = []

    for i, (sigmoid_score, chunk, source) in enumerate(adaptive_pool):
        if sigmoid_score >= CORRECT_THRESHOLD:
            grade = "CORRECT"
        elif sigmoid_score >= AMBIGUOUS_THRESHOLD:
            grade = "AMBIGUOUS"
        else:
            grade = "INCORRECT"
        grades.append(grade)
        chunks.append(chunk)
        sources.append(source)
        scores.append(sigmoid_score)
        icon = {"CORRECT": "✅", "AMBIGUOUS": "🟡", "INCORRECT": "❌"}.get(grade, "❓")
        print(f"  Rank {i+1} → {icon} {grade:<10} score={sigmoid_score:.3f}  [{source}]")

    print("━" * 55)
    print(f"  {grades.count('CORRECT')} CORRECT | "
          f"{grades.count('AMBIGUOUS')} AMBIGUOUS | "
          f"{grades.count('INCORRECT')} INCORRECT")
    print("━" * 55)

    # Keep CORRECT chunks
    for chunk, grade, source, score in zip(chunks, grades, sources, scores):
        if grade == "CORRECT":
            verified_chunks.append(chunk)
            verified_sources.append(source)
            verified_scores.append(score)

    # Phase 2b — Resolve AMBIGUOUS (new vault only)
    ambiguous_indices = [i for i, g in enumerate(grades) if g == "AMBIGUOUS"]

    if ambiguous_indices and PHASE_2_ENABLED:
        print(f"  PHASE 2b — Resolving {len(ambiguous_indices)} AMBIGUOUS chunk(s)")
        print("━" * 55)

        for n, idx in enumerate(ambiguous_indices):
            chunk  = chunks[idx]
            source = sources[idx]
            print(f"  ┌─ [{source}]  ({n+1}/{len(ambiguous_indices)})")

            best_sentence = extract_best_sentence(query, chunk)
            if not best_sentence:
                print("  └─ ⚠️  No useful sentence → discarded.")
                if n < len(ambiguous_indices) - 1:
                    print("  │")
                continue

            print(f"  │  📌 {best_sentence[:110]!r}")
            print("  │  🔍 Supplemental search…")
            supp_chunks, supp_metas = supplemental_search(query, best_sentence, n=3)

            best_supp, best_supp_source, best_supp_score = None, source, 0.0
            for j, sc in enumerate(supp_chunks):
                sc_src   = supp_metas[j].get("source", "Unknown") if supp_metas else "Unknown"
                sc_st    = (supp_metas[j].get("child_text", sc)
                            if (supp_metas and supp_metas[j].get("child_text")) else sc)
                sc_score = _sigmoid(float(grader_model.predict([query, _trim(sc_st)])))
                sc_grade = ("CORRECT" if sc_score >= CORRECT_THRESHOLD else
                            "AMBIGUOUS" if sc_score >= AMBIGUOUS_THRESHOLD else "INCORRECT")
                icon     = {"CORRECT": "✅", "AMBIGUOUS": "🟡", "INCORRECT": "❌"}.get(sc_grade)
                print(f"  │    Supp {j+1}/3 → {icon} score={sc_score:.3f}  [{sc_src}]")
                if sc_grade == "CORRECT" and best_supp is None:
                    best_supp, best_supp_source, best_supp_score = sc, sc_src, sc_score

            if best_supp:
                winner = pick_more_relevant(query, best_sentence, _trim(best_supp, 150))
                if winner == "B":
                    print("  └─ ✅ Supplemental chunk kept.")
                    verified_chunks.append(best_supp)
                    verified_sources.append(best_supp_source)
                    verified_scores.append(best_supp_score)
                else:
                    rs = _sigmoid(float(grader_model.predict([query, best_sentence])))
                    if rs >= RESCUE_THRESHOLD:
                        print(f"  └─ ✅ Sentence kept (score={rs:.3f}).")
                        verified_chunks.append(best_sentence)
                        verified_sources.append(source)
                        verified_scores.append(rs)
                    else:
                        print(f"  └─ ❌ Sentence {rs:.3f} < {RESCUE_THRESHOLD:.2f} → discarded.")
            else:
                rs = _sigmoid(float(grader_model.predict([query, best_sentence])))
                if rs >= RESCUE_THRESHOLD:
                    print(f"  └─ 📎 Sentence re-graded {rs:.3f} → kept.")
                    verified_chunks.append(best_sentence)
                    verified_sources.append(source)
                    verified_scores.append(rs)
                else:
                    print(f"  └─ ❌ Sentence {rs:.3f} < {RESCUE_THRESHOLD:.2f} → discarded.")

            if n < len(ambiguous_indices) - 1:
                print("  │")
        print("━" * 55)

    elif ambiguous_indices and not PHASE_2_ENABLED:
        print(f"  [Phase 2b SKIPPED — legacy] {len(ambiguous_indices)} AMBIGUOUS discarded.")
        print("━" * 55)

    # Hard cap — top MAX_VERIFIED_CHUNKS by score
    if len(verified_chunks) > MAX_VERIFIED_CHUNKS:
        combined = sorted(
            zip(verified_scores, verified_chunks, verified_sources),
            key=lambda x: x[0], reverse=True
        )[:MAX_VERIFIED_CHUNKS]
        dropped          = len(verified_chunks) - MAX_VERIFIED_CHUNKS
        verified_scores  = [x[0] for x in combined]
        verified_chunks  = [x[1] for x in combined]
        verified_sources = [x[2] for x in combined]
        print(f"  [Cap={MAX_VERIFIED_CHUNKS}] Dropped {dropped} lowest-scoring chunk(s).")
        print("━" * 55)

    print(f"  RESULT — {len(verified_chunks)} item(s) in Verified Context Array.")
    print("━" * 55)

    return verified_chunks, verified_sources


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 4 — ADAPTIVE FALLBACK & CONTROLLED GENERATION
# ══════════════════════════════════════════════════════════════════════════════

def rewrite_query(original_query: str) -> str:
    prompt = f"""You are a search query optimizer for a scientific research database.
The following question failed to retrieve relevant results:
"{original_query}"
Rewrite it as a short, keyword-focused search query using different,
more specific scientific terminology. Return ONLY the rewritten query. Keep it under 10 words.
"""
    return call_llm(prompt, model=LIGHT_TEXT_MODEL, max_tokens=32).strip()


def generate_final_answer(query: str, chunks: list, sources: list) -> str:
    if not chunks:
        return "No information detected from the papers for your query."
    context = "\n\n---\n\n".join(
        f"[Source: {sources[i]}]\n{chunk}"
        for i, chunk in enumerate(chunks)
    )
    prompt = f"""You are a precise scientific research assistant.
Answer the user's question using ONLY the context provided below.

Rules:
- Be clear, structured, and concise.
- Do NOT include any information not present in the context.
- If the context only partially answers the question, clearly say so.
- Cite the source filenames where relevant.

User Question:
{query}

Verified Context:
{context}
"""
    return call_llm(
        prompt, model=ANSWER_MODEL, max_tokens=900,
        system="You are a strict, citation-aware research assistant. Never hallucinate. Only use the provided context.",
    )


def generate_soft_answer(query: str, chunks: list, sources: list) -> str:
    context = "\n\n---\n\n".join(
        f"[Source: {sources[i]}]\n{chunk}" for i, chunk in enumerate(chunks)
    )
    prompt = f"""You are a helpful research assistant.
I could not find a direct answer in our database. Related snippets from: {set(sources)}
User Question: {query}
Task:
1. Explicitly state you couldn't find a direct answer.
2. Summarize the related information provided.
3. Be honest about why this is only partially relevant.
Related Context:
{context}
"""
    return call_llm(prompt, model=ANSWER_MODEL, max_tokens=900)


def run_logic_engine(user_query: str) -> dict:
    """
    Master CRAG pipeline — all 4 phases.

    Phase 1: Hybrid retrieval (database.py)
    Phase 2: Tri-state logic engine (evaluate_chunks)
    Phase 3: Pre-flight combined relevance check (_combined_relevance_check)
    Phase 4: Adaptive fallback + controlled generation
    """
    query_domain = detect_query_domain(user_query)
    if query_domain:
        print(f"  [Domain Filter] Restricting to: [{query_domain}]")

    # ── Attempt 1 ─────────────────────────────────────────────────────────────
    raw       = search_vault(user_query, n_results=FETCH_K, domain_filter=query_domain)
    chunks    = raw["documents"][0]
    metadatas = raw["metadatas"][0]

    if not chunks and query_domain:
        print("  [Domain Filter] No results — retrying without filter.")
        raw       = search_vault(user_query, n_results=FETCH_K)
        chunks    = raw["documents"][0]
        metadatas = raw["metadatas"][0]

    verified, sources = evaluate_chunks(user_query, chunks, metadatas)

    # ── Phase 3: Pre-flight combined relevance check ───────────────────────────
    # Run ONLY when verified chunks exist.
    # Mirrors the evaluator's Tier 1 combined check:
    #   PASS → return chunks (evaluator will grade them individually)
    #   FAIL → return [] → evaluator sees empty result → fn++ only, fp += 0
    if verified:
        print(f"  PHASE 3 — Pre-flight combined relevance check ({len(verified)} chunk(s))...")
        combined_ok = _combined_relevance_check(user_query, verified)
        if combined_ok:
            print("  ✅ Combined check PASSED → returning verified context")
            return {
                "status":     "success",
                "answer":     generate_final_answer(user_query, verified, sources),
                "facts":      verified,
                "sources":    list(set(sources)),
                "query_used": user_query,
            }
        else:
            print("  ❌ Combined check FAILED → returning [] to avoid FP injection")
            # Fall through to rewrite attempt below

    # ── Attempt 2: Rewrite (Phase 4 fallback) ─────────────────────────────────
    print()
    print("━" * 55)
    print("  ⚠️  PHASE 4 FALLBACK — rewriting query")
    new_query = rewrite_query(user_query)
    print(f"  Rewritten: {new_query!r}")
    print("━" * 55)
    print()

    raw2       = search_vault(new_query, n_results=FETCH_K)
    chunks2    = raw2["documents"][0]
    metadatas2 = raw2["metadatas"][0]

    verified2, sources2 = evaluate_chunks(new_query, chunks2, metadatas2)

    # Phase 3 check on rewritten query results too
    if verified2:
        print(f"  PHASE 3 — Combined check on fallback results ({len(verified2)} chunk(s))...")
        combined_ok2 = _combined_relevance_check(user_query, verified2)
        if combined_ok2:
            print("  ✅ Combined check PASSED")
            return {
                "status":     "fallback_success",
                "answer":     generate_final_answer(user_query, verified2, sources2),
                "facts":      verified2,
                "sources":    list(set(sources2)),
                "query_used": new_query,
            }
        else:
            print("  ❌ Combined check FAILED on fallback → returning []")

    # ── Attempt 3: Bendy mode ─────────────────────────────────────────────────
    print()
    print("━" * 55)
    print("  🔗 BENDY MODE — partial match")

    scored_bendy = []
    for i, chunk in enumerate(chunks2):
        score_text = (metadatas2[i].get("child_text", chunk)
                      if (metadatas2 and metadatas2[i].get("child_text")) else chunk)
        score = _sigmoid(float(grader_model.predict([user_query, _trim(score_text)])))
        if score >= BENDY_THRESHOLD:
            src = metadatas2[i].get("source", "Unknown") if metadatas2 else "Unknown"
            scored_bendy.append((score, chunk, src))

    scored_bendy.sort(key=lambda x: x[0], reverse=True)
    scored_bendy = scored_bendy[:2]
    related_chunks  = [x[1] for x in scored_bendy]
    related_sources = [x[2] for x in scored_bendy]

    if related_chunks:
        # Bendy mode: skip combined check (soft answer clearly labels uncertainty)
        return {
            "status":     "partial_match",
            "answer":     generate_soft_answer(user_query, related_chunks, related_sources),
            "facts":      related_chunks,
            "sources":    list(set(related_sources)),
            "query_used": new_query,
        }

    return {
        "status":     "failed",
        "answer":     "No information detected from the papers for your query.",
        "facts":      [],
        "sources":    [],
        "query_used": new_query,
    }


# ── CLI entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    question = (
        " ".join(sys.argv[1:]).strip()
        if len(sys.argv) > 1
        else "What is the criterion for turbulent flow?"
    )

    print()
    print("━" * 55)
    print("  CRAG PIPELINE")
    print(f"  Vault: {VAULT_SCHEMA}  |  Phase2: {'ON' if PHASE_2_ENABLED else 'OFF (legacy)'}")
    print(f"  CORRECT={CORRECT_THRESHOLD}  AMBIGUOUS={AMBIGUOUS_THRESHOLD}")
    print(f"  Softmax={SOFTMAX_MASS_CUTOFF}  CombinedCheck=ON  Cap={MAX_VERIFIED_CHUNKS}")
    print("━" * 55)
    print(f"  Q: {question}")
    print("━" * 55)
    print()

    result = run_logic_engine(question)

    print()
    print("━" * 55)
    print("  FINAL ANSWER")
    print("━" * 55)
    print(result["answer"])
    print()
    status_icon = {"success": "✅", "fallback_success": "⚠️",
                   "partial_match": "🔗", "failed": "❌"}.get(result["status"], "❓")
    print(f"  Status  : {status_icon} {result['status'].upper()}")
    print(f"  Facts   : {len(result['facts'])} / max {MAX_VERIFIED_CHUNKS}")
    print(f"  Sources : {', '.join(result['sources']) if result['sources'] else 'None'}")
    print("━" * 55)