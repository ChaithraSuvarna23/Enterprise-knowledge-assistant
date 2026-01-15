from pypdf import PdfReader
import pdfplumber


def extract_text_from_txt(file_path: str) -> str:
    """
    Extract text from a TXT file.
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().strip()


def chunk_text(pages, chunk_size=500, overlap=50):
    chunks = []
    for page in pages:
        words = page["text"].split()
        start = 0

        while start < len(words):
            end = start + chunk_size
            chunk_text = " ".join(words[start:end])

            chunks.append({
                "text": chunk_text,
                "page": page["page"]
            })

            start += chunk_size - overlap

    return chunks



def extract_pages_from_pdf(file_path: str):
    pages = []
    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text:
                pages.append({
                    "page": page_num,
                    "text": text
                })
    return pages