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


def test_chunk_text_handles_overlap_gte_chunk_size() -> None:
    text = "one two three"

    assert chunk_text(text, chunk_size=2, overlap=2) == ["one two"]
