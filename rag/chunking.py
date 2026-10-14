"""Split documents into overlapping chunks.

Strategy: split at "## " headings first, so each chunk is one topic
(e.g. "What payment methods do you accept?"). Mixing topics in one chunk
dilutes its embedding, and short questions then score too low to pass
the relevance gate. Sections longer than the chunk size are packed by
paragraph. Plain text without headings is treated as one section.

Each chunk starts with the document's "# Title" line, so a section like
"## Exchanges" still says it belongs to "Returns & Refunds". A title on
its own would be a useless chunk that takes a retrieval slot.
"""
import re

from rag import config

# Split right before a level-2 heading.
_SECTION_BREAK = re.compile(r"\n(?=## )")


def chunk_text(text: str, size: int = config.CHUNK_SIZE,
               overlap: int = config.CHUNK_OVERLAP) -> list[str]:
    title = ""
    first_line = text.lstrip().split("\n", 1)[0]
    if first_line.startswith("# "):
        title = first_line
        text = text.lstrip()[len(first_line):]

    chunks: list[str] = []
    for section in _SECTION_BREAK.split(text):
        if section.strip():
            for chunk in _chunk_section(section, size, overlap):
                chunks.append(f"{title}\n{chunk}" if title else chunk)
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
