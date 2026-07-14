"""
Split raw resume text into a flat list of meaningful bullet-point / sentence chunks.

Strategy:
  1. Split on newlines first — each non-empty line is a candidate.
  2. Lines that look like section headers (all-caps, short, no verb) or are
     very short (< 15 chars) are discarded rather than kept as context-free noise.
  3. Long lines (paragraphs) are further split on sentence boundaries so no
     single chunk overwhelms the embedding model.

Output is a deduplicated list of stripped strings, order preserved.
"""

import re


# Splits at sentence boundaries: after . ! ? followed by whitespace.
# Uses a lookbehind so the punctuation stays attached to the preceding sentence.
_SENTENCE_SPLIT = re.compile(r'(?<=[.!?])\s+')

# Strips leading whitespace and common bullet/dash characters so the embedding
# sees clean content, not decoration: "• Built a pipeline" → "Built a pipeline"
_BULLET_STRIP = re.compile(r'^[\s•–—\-\*·]+')

# Chunks shorter than this are almost certainly noise (a year, a city name, a
# phone number) that would add nothing to the semantic search.
_MIN_CHUNK_LEN = 15

# Lines longer than this are likely paragraphs rather than single bullets.
# Breaking them at sentence boundaries keeps each chunk focused on one idea,
# which improves cosine similarity accuracy against the job description.
_MAX_LINE_LEN = 300


def _is_header(line: str) -> bool:
    """
    Return True if *line* looks like a resume section header.

    Heuristic: section headers are typically short, all-caps, and contain no
    lowercase letters — e.g. "EXPERIENCE", "EDUCATION", "SKILLS". We keep the
    length cap at 60 chars so a genuine all-caps sentence isn't misclassified.
    """
    if len(line) > 60:
        return False
    # line == line.upper() catches lines with no lowercase; re.search guards
    # against lines that are only punctuation or numbers (e.g. "2020–2023").
    return line == line.upper() and bool(re.search(r'[A-Z]', line))


def chunk_resume(resume_text: str) -> list[str]:
    """
    Parse *resume_text* into a clean, deduplicated list of bullet/sentence chunks.

    Each chunk is a single idea — one accomplishment, one skill, one
    responsibility — stripped of bullet characters and section headers.
    The order of chunks reflects the original document order.

    Args:
        resume_text: Raw text extracted from a resume PDF.

    Returns:
        A list of non-empty strings, each at least _MIN_CHUNK_LEN characters,
        with no duplicates.
    """
    chunks: list[str] = []
    seen: set[str] = set()  # tracks exact strings to prevent duplicates

    for raw_line in resume_text.splitlines():
        # Remove leading bullet markers and surrounding whitespace.
        line = _BULLET_STRIP.sub('', raw_line).strip()

        # Skip blanks, section headers, and lines too short to carry meaning.
        if not line or _is_header(line) or len(line) < _MIN_CHUNK_LEN:
            continue

        # Long lines (paragraphs) are split into individual sentences so each
        # chunk stays focused on a single idea and embeds more accurately.
        candidates = _SENTENCE_SPLIT.split(line) if len(line) > _MAX_LINE_LEN else [line]

        for chunk in candidates:
            chunk = chunk.strip()
            # Guard again after splitting — a sentence fragment may be too short.
            if len(chunk) >= _MIN_CHUNK_LEN and chunk not in seen:
                seen.add(chunk)
                chunks.append(chunk)

    return chunks
