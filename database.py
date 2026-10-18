import fitz
import chromadb
import os
import re
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer

# ── Optional BM25 ──────────────────────────────────────────────────────────────
try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    print("[WARN] rank_bm25 not installed → pip install rank-bm25")
    print("       Falling back to dense-only search.")

# ── Setup ChromaDB ─────────────────────────────────────────────────────────────
chroma_client = chromadb.PersistentClient(path="./vector_vault")

# Child collection  — small 100-word chunks, embedded for precise matching
collection = chroma_client.get_or_create_collection(name="ieee_papers")

# Parent collection — large 350-word chunks, fetched by ID for rich LLM context
parent_collection = chroma_client.get_or_create_collection(name="ieee_papers_parent")

print("Loading BGE-Small Embedding Model (High-Accuracy)...")
model = SentenceTransformer('BAAI/bge-small-en-v1.5')

# ── BM25 cache path ────────────────────────────────────────────────────────────
BM25_CACHE_PATH = "./vector_vault/bm25_corpus.pkl"

# ── Distance threshold ─────────────────────────────────────────────────────────
DISTANCE_THRESHOLD = 0.70

# ── Domain taxonomy ────────────────────────────────────────────────────────────
DOMAIN_KEYWORDS = {
    "computer_networks": ["tcp", "ip", "routing", "protocol", "network", "bandwidth",
                          "latency", "packet", "congestion", "wireless", "subnet"],
    "machine_learning":  ["neural", "gradient", "backpropagation", "training", "loss",
                          "accuracy", "classification", "regression", "overfitting",
                          "transformer", "attention", "embedding"],
    "quantum":           ["qubit", "quantum", "superposition", "entanglement",
                          "decoherence", "hamiltonian", "bloch"],
    "signal_processing": ["fourier", "filter", "frequency", "signal", "sampling",
                          "nyquist", "convolution", "wavelet", "spectral"],
    "security":          ["encryption", "cipher", "cryptography", "attack",
                          "vulnerability", "authentication", "firewall", "malware"],
    "database_systems":  ["sql", "transaction", "acid", "index", "query", "relation",
                          "schema", "join", "normalization"],
    "computer_vision":   ["image", "pixel", "convolution", "cnn", "segmentation",
                          "detection", "recognition", "bounding box", "feature map"],
    "nlp":               ["language model", "tokenize", "parse", "syntax", "semantic",
                          "bert", "gpt", "corpus", "sentiment"],
}


def detect_domain(text: str) -> str:
    text_lower = text.lower()
    hit_counts = {
        domain: sum(1 for kw in keywords if kw in text_lower)
        for domain, keywords in DOMAIN_KEYWORDS.items()
    }
    best = max(hit_counts, key=hit_counts.get)
    return best if hit_counts[best] > 0 else "general"


# ── Vault schema detection ─────────────────────────────────────────────────────

def check_vault_schema():
    """
    Checks whether the current vault was ingested with the new child/parent
    pipeline.  Prints a prominent warning if old-schema chunks are detected.

    The new schema stores every chunk with a 'parent_id' metadata field.
    If 'parent_id' is absent from all chunks, the vault is legacy (350-word
    single chunks with no parent linkage).

    The logic_engine handles both schemas gracefully, but for best results
    the vault should be re-ingested with the current database.py:
        rm -rf ./vector_vault
        python database.py
    """
    try:
        sample = collection.get(limit=5, include=["metadatas"])
        metas  = sample.get("metadatas", [])
        if metas and not any(m.get("parent_id") for m in metas):
            print()
            print("━" * 60)
            print("  ⚠️  LEGACY VAULT DETECTED")
            print("  Chunks have no 'parent_id' — vault was ingested with")
            print("  an older version of database.py.")
            print()
            print("  For best performance, re-ingest:")
            print("    rm -rf ./vector_vault")
            print("    python database.py")
            print()
            print("  The pipeline will run in LEGACY MODE with adjusted")
            print("  thresholds. Expect lower precision / recall than")
            print("  a freshly ingested vault.")
            print("━" * 60)
            print()
            return "legacy"
        return "new"
    except Exception:
        return "unknown"


# ── BM25 helpers ───────────────────────────────────────────────────────────────

def _build_bm25_index():
    all_data = collection.get(include=["documents", "metadatas"])
    docs     = all_data.get("documents", [])
    if not docs:
        return None, [], []
    tokenized = [d.lower().split() for d in docs]
    bm25      = BM25Okapi(tokenized)
    return bm25, docs, all_data.get("metadatas", [])


def _load_or_build_bm25():
    if os.path.exists(BM25_CACHE_PATH):
        try:
            with open(BM25_CACHE_PATH, "rb") as f:
                return pickle.load(f)
        except Exception:
            pass
    bm25, corpus, metadatas = _build_bm25_index()
    if bm25 is not None:
        with open(BM25_CACHE_PATH, "wb") as f:
            pickle.dump((bm25, corpus, metadatas), f)
    return bm25, corpus, metadatas


def invalidate_bm25_cache():
    if os.path.exists(BM25_CACHE_PATH):
        os.remove(BM25_CACHE_PATH)
        print("[BM25] Cache invalidated. Will rebuild on next search.")


def _reciprocal_rank_fusion(ranked_lists: list, k: int = 60) -> list:
    rrf_scores: dict = {}
    for ranked in ranked_lists:
        for rank, item in enumerate(ranked):
            rrf_scores[item] = rrf_scores.get(item, 0.0) + 1.0 / (k + rank + 1)
    return sorted(rrf_scores, key=lambda x: rrf_scores[x], reverse=True)


# ── Chunking ───────────────────────────────────────────────────────────────────

def _chunk_sentences(sentences: list, max_words: int, overlap_words: int) -> list:
    chunks        = []
    current_chunk = []
    current_words = 0

    for sentence in sentences:
        words_in_sentence = len(sentence.split())
        if current_words + words_in_sentence > max_words and current_chunk:
            chunks.append(" ".join(current_chunk))
            overlap_chunk = []
            overlap_count = 0
            for prev_sentence in reversed(current_chunk):
                prev_words = len(prev_sentence.split())
                if overlap_count + prev_words <= overlap_words:
                    overlap_chunk.insert(0, prev_sentence)
                    overlap_count += prev_words
                else:
                    break
            current_chunk = overlap_chunk + [sentence]
            current_words = overlap_count + words_in_sentence
        else:
            current_chunk.append(sentence)
            current_words += words_in_sentence

    if current_chunk:
        chunks.append(" ".join(current_chunk))
    return chunks


def _prepare_sentences(text: str) -> list:
    text = re.sub(r'-\n', '', text)
    text = re.sub(r'\s+', ' ', text)
    return re.split(r'(?<=[.!?]) +', text.strip())


def split_into_sentence_chunks(text, max_words=100, overlap_words=20):
    """100-word child chunks — embedded for precise retrieval."""
    return _chunk_sentences(_prepare_sentences(text), max_words, overlap_words)


def split_into_semantic_chunks(text, max_words=350, overlap_words=75):
    """350-word parent chunks — stored by ID for LLM context."""
    return _chunk_sentences(_prepare_sentences(text), max_words, overlap_words)


# ── Parent expansion ───────────────────────────────────────────────────────────

def _expand_to_parent(child_doc: str, child_meta: dict) -> tuple:
    """
    Returns the parent chunk for LLM context, with child_text stored in metadata
    so logic_engine can score with the focused child text (not the diluted parent).

    If the vault is legacy (no parent_id), returns the chunk unchanged.
    """
    parent_id = child_meta.get("parent_id")
    if not parent_id:
        return child_doc, child_meta

    try:
        result = parent_collection.get(ids=[parent_id], include=["documents", "metadatas"])
        if result["documents"]:
            parent_doc  = result["documents"][0]
            parent_meta = dict(result["metadatas"][0])
            parent_meta["child_text"] = child_doc   # ← key: score with this, not parent
            return parent_doc, parent_meta
    except Exception:
        pass

    return child_doc, child_meta


# ── Ingestion ──────────────────────────────────────────────────────────────────

def process_and_save_pdf(pdf_path):
    file_name = os.path.basename(pdf_path)

    existing = collection.get(where={"source": file_name})
    if len(existing['ids']) > 0:
        print(f" Skipping {file_name}: Already in the vault.")
        return

    doc       = fitz.open(pdf_path)
    full_text = ""
    for page in doc:
        full_text += page.get_text(sort=True) + "\n"

    domain = detect_domain(full_text)
    print(f" Detected domain for {file_name}: [{domain}]")

    child_chunks  = split_into_sentence_chunks(full_text)
    parent_chunks = split_into_semantic_chunks(full_text)

    # Store parent chunks (no embedding — fetched by ID only)
    dummy_dim        = 384
    dummy_vecs       = [[0.0] * dummy_dim for _ in parent_chunks]
    parent_ids       = [f"{file_name}_parent_{i}" for i in range(len(parent_chunks))]
    parent_metadatas = [{"source": file_name, "domain": domain} for _ in parent_chunks]

    parent_collection.add(
        embeddings=dummy_vecs,
        documents=parent_chunks,
        metadatas=parent_metadatas,
        ids=parent_ids,
    )

    # Store child chunks (embedded for retrieval)
    ratio           = max(1, len(child_chunks) // max(1, len(parent_chunks)))
    child_ids       = []
    child_metadatas = []

    for i in range(len(child_chunks)):
        parent_idx = min(i // ratio, len(parent_chunks) - 1)
        child_ids.append(f"{file_name}_child_{i}")
        child_metadatas.append({
            "source":    file_name,
            "domain":    domain,
            "parent_id": f"{file_name}_parent_{parent_idx}",
        })

    print(f"Translating {len(child_chunks)} child chunks from {file_name}...")
    prefixed = [
        f"Represent this sentence for searching relevant passages: {c}"
        for c in child_chunks
    ]
    vectors = model.encode(prefixed, show_progress_bar=False).tolist()

    collection.add(
        embeddings=vectors,
        documents=child_chunks,
        metadatas=child_metadatas,
        ids=child_ids,
    )
    print(f" Saved {file_name} ({len(child_chunks)} child + {len(parent_chunks)} parent chunks)")
    invalidate_bm25_cache()


# ── Retrieval ──────────────────────────────────────────────────────────────────

# Set by api.py before calling run_logic_engine to restrict retrieval to one file.
# Reset to None after the call. Core pipeline logic is unaware of this.
_ACTIVE_FILE_FILTER: str | None = None


def search_vault(query, n_results=10, domain_filter=None):
    """
    Hybrid Search (Dense + BM25) + RRF + Parent expansion.
    Returns parent chunks in documents[], child_text in metadatas[] for scoring.
    Respects _ACTIVE_FILE_FILTER (set by api.py) to restrict to a single source.
    """
    fetch_n = n_results * 3

    search_query = f"Represent this sentence for searching relevant passages: {query}"
    query_vector = model.encode([search_query]).tolist()

    # Build ChromaDB where clause — respect both domain filter and active file filter
    active_src = _ACTIVE_FILE_FILTER
    if active_src and domain_filter:
        where_filter = {"$and": [{"source": active_src}, {"domain": domain_filter}]}
    elif active_src:
        where_filter = {"source": active_src}
    elif domain_filter:
        where_filter = {"domain": domain_filter}
    else:
        where_filter = None

    results = collection.query(
        query_embeddings=query_vector,
        n_results=min(fetch_n, 100),
        include=["documents", "metadatas", "distances"],
        where=where_filter,
    )

    raw_docs      = results["documents"][0]
    raw_metas     = results["metadatas"][0]
    raw_distances = results["distances"][0]

    doc_info: dict = {}
    for doc, meta, dist in zip(raw_docs, raw_metas, raw_distances):
        doc_info[doc] = (meta, dist)

    dense_ranking = list(raw_docs)

    # BM25 sparse retrieval
    bm25_ranking = []
    if BM25_AVAILABLE:
        try:
            bm25, corpus, bm25_metas = _load_or_build_bm25()
            if bm25 and corpus:
                tokenized_query = query.lower().split()
                scores          = bm25.get_scores(tokenized_query)
                top_n           = min(fetch_n, len(corpus))
                top_indices     = np.argsort(scores)[::-1][:top_n]

                for idx in top_indices:
                    doc  = corpus[idx]
                    meta = bm25_metas[idx] if bm25_metas else {}
                    if domain_filter and meta.get("domain") != domain_filter:
                        continue
                    if active_src and meta.get("source") != active_src:
                        continue
                    bm25_ranking.append(doc)
                    if doc not in doc_info:
                        doc_info[doc] = (meta, DISTANCE_THRESHOLD)
        except Exception as e:
            print(f"  [BM25] Error: {e}")

    all_rankings = [r for r in [dense_ranking, bm25_ranking] if r]
    if len(all_rankings) > 1:
        merged_ranking = _reciprocal_rank_fusion(all_rankings)
        print(f"  [Hybrid] Dense={len(dense_ranking)} | BM25={len(bm25_ranking)} → merged={len(merged_ranking)}")
    else:
        merged_ranking = dense_ranking
        print(f"  [Dense-only] Retrieved {len(dense_ranking)} chunks")

    filtered_docs  = []
    filtered_metas = []

    for doc in merged_ranking[:fetch_n]:
        meta, dist = doc_info.get(doc, ({}, DISTANCE_THRESHOLD))
        if dist <= DISTANCE_THRESHOLD:
            expanded_doc, expanded_meta = _expand_to_parent(doc, meta)
            filtered_docs.append(expanded_doc)
            filtered_metas.append(expanded_meta)
        else:
            src = meta.get("source", "Unknown")
            print(f"  [pre-filter] Dropped '{src}' — distance={dist:.3f} > {DISTANCE_THRESHOLD}")

    print(f"  [DB] {len(merged_ranking)} merged → {len(filtered_docs)} passed pre-filter")

    results["documents"][0] = filtered_docs
    results["metadatas"][0] = filtered_metas
    return results


# ── API helpers (used by api.py, not core pipeline) ────────────────────────────

def list_documents() -> list:
    """Return a summary of all unique source documents in the vault."""
    try:
        all_data = collection.get(include=["metadatas"])
        metas = all_data.get("metadatas", [])
        ids = all_data.get("ids", [])
        source_counts: dict = {}
        for meta in metas:
            src = meta.get("source", "Unknown")
            source_counts[src] = source_counts.get(src, 0) + 1
        return [
            {"id": src, "filename": src, "chunks": count,
             "indexedAt": "", "fileType": "pdf"}
            for src, count in source_counts.items()
        ]
    except Exception:
        return []


def delete_document(filename: str) -> int:
    """Delete all chunks (child + parent) for a given source filename."""
    deleted = 0
    try:
        # Delete child chunks
        child_data = collection.get(where={"source": filename})
        child_ids = child_data.get("ids", [])
        if child_ids:
            collection.delete(ids=child_ids)
            deleted += len(child_ids)

        # Delete parent chunks
        parent_data = parent_collection.get(where={"source": filename})
        parent_ids = parent_data.get("ids", [])
        if parent_ids:
            parent_collection.delete(ids=parent_ids)
            deleted += len(parent_ids)

        invalidate_bm25_cache()
    except Exception as e:
        print(f"[delete_document] Error: {e}")
    return deleted


# ── CLI / batch ingestion ──────────────────────────────────────────────────────
if __name__ == "__main__":
    paper_folder = "papers"
    if not os.path.exists(paper_folder):
        os.makedirs(paper_folder)
        print(f"Please put your PDFs in the '{paper_folder}' folder.")

    pdf_files = [f for f in os.listdir(paper_folder) if f.endswith('.pdf')]
    print(f" Found {len(pdf_files)} papers. Starting upload...")

    for filename in pdf_files:
        path = os.path.join(paper_folder, filename)
        try:
            process_and_save_pdf(path)
        except Exception as e:
            print(f" Error with {filename}: {e}")

    print("\n DATABASE READY.")