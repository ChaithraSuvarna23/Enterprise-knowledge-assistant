from pypdf import PdfReader

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file.
    """
    reader = PdfReader(file_path)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text.strip()


def extract_text_from_txt(file_path: str) -> str:
    """
    Extract text from a TXT file.
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().strip()


def chunk_text(
    text: str,
    chunk_size: int = 800,
    overlap: int = 150
) -> list[str]:
    """
    Split text into overlapping chunks.
    """
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk.strip())

        start = end - overlap  # overlap to preserve context

    return chunks
