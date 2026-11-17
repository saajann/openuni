import pytest

from ingestion.chunking.text_splitter import chunk_text


def test_chunk_text_splits_text_into_word_chunks() -> None:
    text = "one two three four five six seven eight"

    assert chunk_text(text, chunk_size=3, overlap=0) == [
        "one two three",
        "four five six",
        "seven eight",
    ]


def test_chunk_text_returns_empty_list_for_empty_string() -> None:
    assert chunk_text("", chunk_size=5, overlap=1) == []


def test_chunk_text_overlaps_chunks_by_requested_words() -> None:
    text = "one two three four five six seven"

    assert chunk_text(text, chunk_size=3, overlap=1) == [
        "one two three",
        "three four five",
        "five six seven",
        "seven",
    ]


@pytest.mark.parametrize("text", ["", "one two three four five six"])
@pytest.mark.parametrize(
    ("chunk_size", "overlap"),
    [(0, 0), (-1, 0), (2, -1), (2, 2), (2, 3)],
)
def test_chunk_text_rejects_invalid_parameters(text: str, chunk_size: int, overlap: int) -> None:
    with pytest.raises(ValueError):
        chunk_text(text, chunk_size=chunk_size, overlap=overlap)


@pytest.mark.parametrize(
    ("chunk_size", "overlap"),
    [(1, 0), (2, 0), (2, 1), (3, 2), (5, 1), (20, 19), (500, 50)],
)
def test_chunk_text_preserves_all_words_for_valid_parameters(chunk_size: int, overlap: int) -> None:
    words = [f"word{i}" for i in range(11)]

    chunks = chunk_text(" ".join(words), chunk_size=chunk_size, overlap=overlap)

    assert all(0 < len(chunk.split()) <= chunk_size for chunk in chunks)
    reconstructed = chunks[0].split() + [
        word for chunk in chunks[1:] for word in chunk.split()[overlap:]
    ]
    assert reconstructed == words
