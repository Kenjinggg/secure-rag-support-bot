"""Split documents into overlapping chunks.

Strategy: split at "## " headings first, so each chunk is one topic
(e.g. "What payment methods do you accept?"). Mixing topics in one chunk
dilutes its embedding, and short questions then score too low to pass
the relevance gate. Sections longer than the chunk size are packed by
paragraph. Plain text without headings is treated as one section.
"""
import re

from rag import config

# Split right before a level-2 heading; the "# Title" line stays
# attached to the first section instead of becoming a chunk on its own.
_SECTION_BREAK = re.compile(r"\n(?=## )")


def chunk_text(text: str, size: int = config.CHUNK_SIZE,
               overlap: int = config.CHUNK_OVERLAP) -> list[str]:
    chunks: list[str] = []
    for section in _SECTION_BREAK.split(text):
        if section.strip():
            chunks.extend(_chunk_section(section, size, overlap))
    return chunks


def _chunk_section(text: str, size: int, overlap: int) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        # A single paragraph longer than the chunk size gets hard-split.
        if len(para) > size:
            if current:
                chunks.append(current)
                current = ""
            start = 0
            while start < len(para):
                chunks.append(para[start:start + size])
                start += size - overlap
            continue

        if len(current) + len(para) + 2 <= size:
            current = f"{current}\n\n{para}" if current else para
        else:
            chunks.append(current)
            # Carry the tail of the previous chunk forward as overlap,
            # so facts that straddle a boundary aren't lost.
            tail = current[-overlap:] if overlap else ""
            current = f"{tail}\n\n{para}" if tail else para

    if current:
        chunks.append(current)
    return chunks
