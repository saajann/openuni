import os

try:
    import fitz  # PyMuPDF
except ModuleNotFoundError:  # pragma: no cover - exercised when PyMuPDF is absent
    fitz = None


def load_txt(filepath: str) -> str:
    with open(filepath, encoding="utf-8") as f:
        return f.read()


def load_pdf(filepath: str) -> str:
    if fitz is None:
        raise ModuleNotFoundError("No module named 'fitz'. Install PyMuPDF to load PDF files.")

    doc = fitz.open(filepath)
    text = ""
    for page in doc:
        text += page.get_text() + "\n"
    return text


def load_document(filepath: str) -> str:
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".txt" or ext == ".md":
        return load_txt(filepath)
    elif ext == ".pdf":
        return load_pdf(filepath)
    else:
        raise ValueError(f"Unsupported file format: {ext}")
