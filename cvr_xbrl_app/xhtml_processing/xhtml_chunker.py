# xhtml_chunker.py
"""
Utility for chunking long narrative text into reasonably sized pieces
for LLM processing.

We chunk on paragraph boundaries (blank lines) to keep structure,
not in the middle of sentences.
"""

from typing import List
import re


def chunk_text(text: str, max_chars: int = 9000) -> List[str]:
    """
    Split text into chunks of approximately max_chars characters,
    using paragraph boundaries.

    - We split on blank lines (one or more newlines with optional spaces)
    - We then greedily pack paragraphs until the chunk would exceed max_chars
    - No overlap by default (can be added later if needed)
    """
    if not text:
        return []

    paragraphs = re.split(r"\n\s*\n", text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    chunks: List[str] = []
    current_paras: List[str] = []
    current_len = 0

    for para in paragraphs:
        # +2 for the blank lines we re-insert between paragraphs
        added_len = len(para) + (2 if current_paras else 0)

        if current_paras and current_len + added_len > max_chars:
            # flush current chunk
            chunks.append("\n\n".join(current_paras))
            current_paras = [para]
            current_len = len(para)
        else:
            current_paras.append(para)
            current_len += added_len

    if current_paras:
        chunks.append("\n\n".join(current_paras))

    return chunks
