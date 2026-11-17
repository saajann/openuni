import re


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Splits text into chunks of roughly `chunk_size` words,
    with an overlap of `overlap` words.
    For v0, we use a simple word-based splitting approach which is fast and
    requires no extra dependencies.

    Raises:
        ValueError: If chunk_size is not positive or overlap is outside
            the range 0 <= overlap < chunk_size.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")

    words = re.findall(r"\S+", text)
    chunks = []

    if not words:
        return []

    i = 0
    while i < len(words):
        chunk_words = words[i : i + chunk_size]
        chunks.append(" ".join(chunk_words))
        i += chunk_size - overlap

    return chunks
