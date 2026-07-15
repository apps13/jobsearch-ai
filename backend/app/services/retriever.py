"""
Hybrid retrieval for resume bullets: dense (semantic) + sparse (keyword) via RRF.

Pipeline:
    resume text → chunk_resume → list[str]
                                      |
              ┌───────────────────────┴───────────────────────┐
              │  Dense                                Sparse   │
              │  embed_texts(chunks)              BM25Okapi    │
              │  embed_texts([job_description])   .get_scores  │
              │  dot product → dense_scores       bm25_scores  │
              └───────────────────────┬───────────────────────┘
                                      │
                          Reciprocal Rank Fusion
                          score = Σ 1 / (k + rank)
                                      │
                              top-k → list[str]

Why hybrid over dense-only:
  Dense retrieval captures semantic similarity ("built pipelines" matches
  "data engineering experience") but can miss exact keyword matches that matter
  to an ATS or recruiter ("Python", "AWS", specific job titles). BM25 catches
  those exact terms. RRF merges both ranked lists without requiring score
  normalisation — rank position is the only input, so the two scoring scales
  never need to be reconciled.
"""

import numpy as np
from rank_bm25 import BM25Okapi

from app.services.chunker import chunk_resume
from app.services.embedder import embed_texts

_DEFAULT_TOP_K = 15

# Standard RRF constant. Higher k reduces the impact of top-ranked results,
# making the fusion more conservative. 60 is the value used in the original
# RRF paper and works well in practice for small candidate sets.
_RRF_K = 60


def _bm25_scores(chunks: list[str], query: str) -> np.ndarray:
    """
    Score each chunk against *query* using BM25Okapi keyword matching.

    BM25 tokenises by whitespace and lowercases. Returns a float array of
    shape (len(chunks),) where higher = more keyword overlap with the query.

    Args:
        chunks: Tokenised corpus — one string per resume bullet.
        query:  The job description text used as the BM25 query.

    Returns:
        numpy array of BM25 scores, one per chunk.
    """
    # BM25 expects a list of token lists for the corpus and a token list for
    # the query. Simple whitespace split is sufficient here — the goal is
    # keyword overlap, not linguistic analysis.
    tokenised_corpus = [chunk.lower().split() for chunk in chunks]
    tokenised_query = query.lower().split()

    bm25 = BM25Okapi(tokenised_corpus)
    return np.array(bm25.get_scores(tokenised_query), dtype=np.float32)


def _dense_scores(chunks: list[str], job_description: str) -> np.ndarray:
    """
    Score each chunk against *job_description* using cosine similarity.

    Embeds all chunks and the query via the OpenAI API. Because vectors are
    L2-normalised by the API, dot product equals cosine similarity directly.

    Args:
        chunks:          Resume bullets to embed.
        job_description: Job posting text used as the query.

    Returns:
        numpy array of cosine similarity scores, one per chunk.
    """
    chunk_embeddings = embed_texts(chunks)            # shape: (n, 1536)
    query_embedding = embed_texts([job_description])  # shape: (1, 1536)

    # Each row dotted with the query vector gives its cosine similarity.
    return chunk_embeddings @ query_embedding[0]      # shape: (n,)


def _rrf_fusion(
    scores_a: np.ndarray,
    scores_b: np.ndarray,
    k: int = _RRF_K,
) -> np.ndarray:
    """
    Combine two score arrays into a single fused ranking via Reciprocal Rank Fusion.

    Each array is converted to a rank list (rank 0 = highest score). The RRF
    contribution for a chunk at rank r is 1 / (k + r). Contributions from both
    lists are summed, so a chunk ranked highly in both gets a significantly
    higher fused score than one ranked highly in only one.

    Args:
        scores_a: Score array from the first retrieval method (e.g. dense).
        scores_b: Score array from the second retrieval method (e.g. BM25).
        k:        RRF constant controlling rank-score steepness.

    Returns:
        Fused score array of the same length. Higher = more relevant overall.
    """
    n = len(scores_a)

    # argsort ascending, then argsort again to get rank positions (0 = best).
    ranks_a = np.argsort(np.argsort(-scores_a))
    ranks_b = np.argsort(np.argsort(-scores_b))

    return (1.0 / (k + ranks_a) + 1.0 / (k + ranks_b)).astype(np.float32)


def retrieve_relevant_bullets(
    resume_text: str,
    job_description: str,
    top_k: int = _DEFAULT_TOP_K,
) -> list[str]:
    """
    Return the *top_k* resume bullets most relevant to *job_description*.

    Uses hybrid retrieval: BM25 keyword scores and dense cosine similarity
    scores are each converted to ranks, then merged via Reciprocal Rank Fusion.
    The final ranking reflects both semantic relevance and keyword overlap.

    Args:
        resume_text:     Raw resume string (from PDF extraction or user paste).
        job_description: Full job posting text, used as both BM25 and dense query.
        top_k:           Maximum bullets to return. If fewer chunks exist, all
                         are returned in fused-score order.

    Returns:
        Ordered list of bullet strings, highest fused score first. Empty list
        if the resume produces no usable chunks (e.g. unreadable PDF).
    """
    chunks = chunk_resume(resume_text)

    # If the resume is unreadable or empty after cleaning, return nothing.
    # CoverLetterService falls back to the full resume text in this case.
    if not chunks:
        return []

    # Run both retrieval methods independently — they use different signals
    # and neither depends on the output of the other.
    sparse = _bm25_scores(chunks, job_description)
    dense = _dense_scores(chunks, job_description)

    # Merge via RRF — rank positions from both methods are combined so that
    # bullets appearing near the top of both lists score highest overall.
    fused = _rrf_fusion(dense, sparse)

    k = min(top_k, len(chunks))

    # argpartition finds the top-k indices in O(n), then argsort orders them.
    top_indices = np.argpartition(fused, -k)[-k:]
    top_indices = top_indices[np.argsort(fused[top_indices])[::-1]]  # descending

    return [chunks[i] for i in top_indices]
