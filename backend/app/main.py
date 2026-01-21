from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import shutil
import uuid

# ---------- Internal imports ----------
from app.config import UPLOAD_DIR
from app.utils import (
    extract_pages_from_pdf,
    extract_text_from_txt,
    chunk_text,
)
from app.vector_store import store_chunks, search_chunks
from app.reranker import rerank_chunks
from app.context_builder import build_context

from app.llm import generate_answer
from app.memory import get_chat_history, append_message

# ---------- App ----------
app = FastAPI(
    title="Enterprise Knowledge Assistant",
    description="RAG-based backend for querying enterprise documents",
    version="1.0.0",
)

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Health ----------
@app.get("/health")
def health_check():
    return {"status": "ok"}

# ============================================================
# 📤 UPLOAD ENDPOINT
# ============================================================
@app.post("/upload")
def upload_document(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix.lower()

    if ext not in [".pdf", ".txt"]:
        raise HTTPException(status_code=400, detail="Only PDF and TXT supported")

    unique_name = f"{uuid.uuid4()}_{file.filename}"
    upload_path = UPLOAD_DIR / unique_name

    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # -------- Extract text --------
    if ext == ".pdf":
        pages = extract_pages_from_pdf(upload_path)
        chunks = chunk_text(pages)
    else:
        text = extract_text_from_txt(upload_path)
        if not text.strip():
            raise HTTPException(status_code=400, detail="Empty TXT file")

        pages = [{"page": 1, "text": text}]
        chunks = chunk_text(pages)

    if not chunks:
        raise HTTPException(status_code=400, detail="Chunking failed")

    store_chunks(chunks, source=file.filename)

    return {
        "filename": file.filename,
        "chunks_indexed": len(chunks),
        "status": "indexed",
    }

# ============================================================
# 🔎 QUERY ENDPOINT (FINAL TUNED VERSION)
# ============================================================
@app.post("/query")
def query_knowledge_base(
    question: str,
    session_id: str = Query(...)
):
    question = question.lower().strip()
    
    # 1️⃣ Load chat history (for memory only, NOT context)
    chat_history = get_chat_history(session_id)

    # 2️⃣ Save user message
    append_message(session_id, "user", question)

    # 3️⃣ Vector search (higher recall)
    results = search_chunks(question, top_k=12)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        answer = "No relevant information found in the documents."
        append_message(session_id, "assistant", answer)
        return {
            "question": question,
            "answer": answer,
            "sources": [],
        }

    # 4️⃣ RERANK (semantic + keyword overlap)
    reranked = rerank_chunks(
        documents,
        metadatas,
        distances,
        question,
    )

    # Take top 3 after reranking
    top_chunks = reranked[:3]
    is_section_query = len(question.split()) <= 4

    if is_section_query:
        candidate_chunks = [c[1] for c in reranked[:5]]
    else:
        candidate_chunks = [c[1] for c in reranked[:3]]


    # 6️⃣ Build DOCUMENT‑ONLY context (CRITICAL)
    context = build_context(candidate_chunks, max_tokens=1400)

    # 7️⃣ Generate answer (Groq / LLM)
    answer = generate_answer(question, candidate_chunks)

    # 8️⃣ Save assistant reply
    append_message(session_id, "assistant", answer)

    # 9️⃣ Source attribution (top chunk)
    best_meta = top_chunks[0][2]
    best_dist = top_chunks[0][3]

    return {
        "question": question,
        "answer": answer,
        "sources": [
            {
                "source": best_meta.get("source"),
                "page": best_meta.get("page"),
                "chunk_id": best_meta.get("chunk_id"),
                "distance": round(best_dist, 3),
            }
        ],
    }

# ============================================================
# 🔍 RETRIEVE‑ONLY (DEBUG / UI SUPPORT)
# ============================================================
@app.post("/query/retrieve-only")
def retrieve_only(
    question: str,
    top_k: int = 5,
    min_distance: float = 1.1,
):
    results = search_chunks(question, top_k=top_k, min_distance=min_distance)

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    return {
        "question": question,
        "results": [
            {
                "chunk_id": meta["chunk_id"],
                "source": meta["source"],
                "page": meta["page"],
                "distance": round(dist, 3),
                "text": doc,
            }
            for doc, meta, dist in zip(documents, metadatas, distances)
        ],
    }
