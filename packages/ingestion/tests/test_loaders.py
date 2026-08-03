from types import SimpleNamespace

import pytest

from ingestion.loaders import local


def test_load_txt_reads_utf8_file(tmp_path) -> None:
    filepath = tmp_path / "notes.txt"
    filepath.write_text("hello openuni", encoding="utf-8")

    assert local.load_txt(str(filepath)) == "hello openuni"


def test_load_document_supports_markdown_files(tmp_path) -> None:
    filepath = tmp_path / "readme.md"
    filepath.write_text("# OpenUni", encoding="utf-8")

    assert local.load_document(str(filepath)) == "# OpenUni"


def test_load_pdf_joins_page_text_with_newlines(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakePage:
        def get_text(self) -> str:
            return "Course catalog"

    class FakeDocument:
        def __init__(self) -> None:
            self.pages = [FakePage(), FakePage()]

        def __iter__(self):
            return iter(self.pages)

    monkeypatch.setattr(local, "fitz", SimpleNamespace(open=lambda _: FakeDocument()))

    assert local.load_pdf("catalog.pdf") == "Course catalog\nCourse catalog\n"


def test_load_document_raises_for_unsupported_extension() -> None:
    with pytest.raises(ValueError, match="Unsupported file format: .csv"):
        local.load_document("data.csv")
