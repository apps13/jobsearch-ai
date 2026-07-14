"""
Embed a list of strings using OpenAI text-embedding-3-small.

Returns a 2-D numpy array of shape (n_texts, embedding_dim).
Each row is L2-normalised by the API, so dot product == cosine similarity.

Why text-embedding-3-small:
  Cheaper and faster than text-embedding-3-large with only a modest accuracy
  drop. 1536-dimensional output is a good balance between expressiveness and
  memory cost for in-memory search over ~20–50 resume bullets.
"""

import numpy as np
from openai import OpenAI

from app.core.config import settings

_EMBED_MODEL = "text-embedding-3-small"

# Stay well under the API limit of 2048 inputs per call. 100 is a safe ceiling
# that avoids hitting payload-size limits on long chunks as well.
_BATCH_SIZE = 100


def embed_texts(texts: list[str]) -> np.ndarray:
    """
    Call the OpenAI Embeddings API and return a 2-D float32 numpy array.

    Each row i is the embedding vector for texts[i]. Vectors are L2-normalised
    by the API, so the dot product of any two rows equals their cosine
    similarity — no normalisation step needed in the caller.

    Args:
        texts: List of strings to embed. May be empty.

    Returns:
        numpy array of shape (len(texts), 1536), dtype float32.
        Returns an empty (0, 1536) array when *texts* is empty so callers
        don't need to special-case the length check.
    """
    # Return a correctly shaped empty array rather than raising, so retriever.py
    # can handle the no-chunks case without a special branch here.
    if not texts:
        return np.empty((0, 1536), dtype=np.float32)

    client = OpenAI(api_key=settings.openai_api_key)
    vectors: list[list[float]] = []

    # Process in batches to stay within API limits. For typical resumes
    # (20–50 chunks) this will be a single call; batching handles edge cases
    # like very long resumes without any code change.
    for i in range(0, len(texts), _BATCH_SIZE):
        batch = texts[i : i + _BATCH_SIZE]
        response = client.embeddings.create(model=_EMBED_MODEL, input=batch)

        # The API documents that items are returned in the same order as the
        # input, but we sort by index explicitly as a defensive measure.
        items = sorted(response.data, key=lambda e: e.index)
        vectors.extend(item.embedding for item in items)

    # Convert to float32 (not float64) — sufficient precision for cosine
    # similarity and halves the memory footprint of the array.
    return np.array(vectors, dtype=np.float32)
