from pypdf import PdfReader
import pdfplumber


def extract_text_from_txt(file_path: str) -> str:
    """
    Extract text from a TXT file.
    """
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().strip()


def chunk_text(pages, chunk_size=500, overlap=50):
    all_text = []
    for page in pages:
        all_text.append(page["text"])

    full_text = " ".join(all_text)
    words = full_text.split()

    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])

        chunks.append({
            "text": chunk,
            "page": -1
        })

        start += chunk_size - overlap

    return chunks




def extract_pages_from_pdf(file_path: str):
    pages = []
    current_heading = None

    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if not text:
                continue

            lines = text.split("\n")
            processed_lines = []

            for line in lines:
                clean = line.strip()
                if not clean:
                    continue

                # 🔹 HEADING DETECTION (generic)
                if (
                    clean.isupper()
                    or (clean.istitle() and len(clean.split()) <= 6)
                ):
                    current_heading = clean
                    continue

                # 🔹 Attach heading to content
                if current_heading:
                    processed_lines.append(
                        f"{current_heading}: {clean}"
                    )
                else:
                    processed_lines.append(clean)

            pages.append({
                "page": page_num,
                "text": " ".join(processed_lines)
            })

    return pages
