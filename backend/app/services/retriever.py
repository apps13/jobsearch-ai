"""
In-memory RAG retrieval for resume bullets.

Given a resume string and a query string (the job description), returns the
top-k resume bullets that are most semantically similar to the query.

Everything lives in memory for the duration of one request — no vector DB,
no persistent index. This is intentional: resume chunks are small (< 100
items), so an in-memory dot product is faster than any network round-trip
to an external store.

Pipeline:
    resume text → chunk_resume → list[str]
                                    ↓
                              embed_texts   ← chunk_embeddings (n, 1536)
                              embed_texts   ← query_embedding  (1, 1536)
                                    ↓
                           dot product → scores (n,)
                                    ↓
                          top-k selection → list[str]
"""

import numpy as np

from app.services.chunker import chunk_resume
from app.services.embedder import embed_texts

# 15 bullets is enough context for the LLM to write a specific cover letter
# without overwhelming it with the entire resume. Tune this if quality testing
# shows important experience being left out.
_DEFAULT_TOP_K = 15


def retrieve_relevant_bullets(
    resume_text: str,
    job_description: str,
    top_k: int = _DEFAULT_TOP_K,
) -> list[str]:
    """
    Return the *top_k* resume bullets most semantically relevant to *job_description*.

    Runs the full RAG retrieval pipeline in memory:
      1. Chunk the resume into individual bullets/sentences.
      2. Embed all chunks and the job description via the OpenAI API.
      3. Score each chunk by cosine similarity to the job description.
      4. Return the highest-scoring chunks in descending order.

    Args:
        resume_text:     Raw resume string (from PDF extraction or user paste).
        job_description: The full job posting text, used as the search query.
        top_k:           Maximum number of bullets to return. If the resume
                         yields fewer chunks than top_k, all chunks are returned.

    Returns:
        Ordered list of bullet strings, most relevant first. Empty list if the
        resume produces no usable chunks (e.g. unreadable PDF).
    """
    chunks = chunk_resume(resume_text)

    # If the resume is unreadable or empty after cleaning, return nothing.
    # The caller (CoverLetterService) falls back to the full resume text.
    if not chunks:
        return []

    # Two separate API calls: one for all resume chunks, one for the query.
    # Keeping them separate makes batching logic in embed_texts straightforward
    # and means the query vector is never mixed into the chunk matrix indices.
    chunk_embeddings = embed_texts(chunks)            # shape: (n_chunks, 1536)
    query_embedding = embed_texts([job_description])  # shape: (1, 1536)

    # Matrix multiply: each row of chunk_embeddings dotted with the single
    # query vector. Because both are L2-normalised, each result is the cosine
    # similarity between that chunk and the job description (-1 to 1 range,
    # higher = more semantically similar).
    scores: np.ndarray = chunk_embeddings @ query_embedding[0]  # shape: (n_chunks,)

    # Clamp k to the number of available chunks — argpartition requires k < n.
    k = min(top_k, len(chunks))

    # np.argpartition is O(n) vs O(n log n) for a full sort. It guarantees the
    # last k entries of the result are the k largest, but in arbitrary order.
    # We then sort only those k indices by score to get the final ranking.
    top_indices = np.argpartition(scores, -k)[-k:]
    top_indices = top_indices[np.argsort(scores[top_indices])[::-1]]  # descending

    return [chunks[i] for i in top_indices]
