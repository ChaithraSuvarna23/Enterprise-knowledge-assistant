from fastapi import FastAPI, UploadFile, File, HTTPException
from pathlib import Path
import shutil
import uuid

from app.config import UPLOAD_DIR, EXTRACTED_DIR
from app.utils import extract_text_from_pdf, extract_text_from_txt,chunk_text
from app.vector_store import store_chunks, search_chunks

app = FastAPI(
    title="Enterprise Knowledge Assistant",
    description="RAG-based backend for querying enterprise documents",
    version="0.1.0"
)

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/upload")
def upload_document(file: UploadFile = File(...)):
    """
    Upload a PDF or TXT document and extract text from it.
    """

    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in [".pdf", ".txt"]:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported"
        )

    # Save uploaded file
    unique_name = f"{uuid.uuid4()}_{file.filename}"
    upload_path = UPLOAD_DIR / unique_name
    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract text
    if file_ext == ".pdf":
        extracted_text = extract_text_from_pdf(upload_path)
    else:
        extracted_text = extract_text_from_txt(upload_path)

    if not extracted_text:
        raise HTTPException(
            status_code=400,
            detail="No text could be extracted from the document"
        )

    # Save extracted text
    extracted_path = EXTRACTED_DIR / f"{upload_path.stem}.txt"
    with open(extracted_path, "w", encoding="utf-8") as f:
        f.write(extracted_text)

    chunks = chunk_text(extracted_text)
    store_chunks(chunks, source=file.filename)

    return {
        "filename": file.filename,
        "characters_extracted": len(extracted_text),
        "total_chunks": len(chunks),
        "status": "indexed"
    }


@app.post("/query")
def query_knowledge_base(question: str):
    """
    Query enterprise documents using semantic search.
    """
    results = search_chunks(question)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    response = []

    for doc, meta in zip(documents, metadatas):
        response.append({
            "content": doc,
            "source": meta.get("source"),
            "chunk_id": meta.get("chunk_id")
        })

    return {
        "question": question,
        "results": response
    }
