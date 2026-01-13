from fastapi import FastAPI, UploadFile, File, HTTPException
from pathlib import Path
import shutil
import uuid
from app.llm import generate_answer
from app.evaluation import precision_at_k, average_distance,recall
from fastapi import Query



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
    Upload a PDF or TXT document, extract text, clean it,
    chunk it, and store embeddings.
    """

    file_ext = Path(file.filename).suffix.lower()

    if file_ext not in [".pdf", ".txt"]:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and TXT files are supported"
        )

    # 1️⃣ Save uploaded file
    unique_name = f"{uuid.uuid4()}_{file.filename}"
    upload_path = UPLOAD_DIR / unique_name

    with open(upload_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2️⃣ Extract text
    if file_ext == ".pdf":
        extracted_text = extract_text_from_pdf(upload_path)
    else:
        extracted_text = extract_text_from_txt(upload_path)

    if not extracted_text or not extracted_text.strip():
        raise HTTPException(
            status_code=400,
            detail="No readable text could be extracted from the document"
        )

    # 3️⃣ CLEAN text (🔑 fixes UnicodeEncodeError)
    clean_text = (
        extracted_text
        .encode("utf-8", errors="ignore")
        .decode("utf-8")
    )

    # 4️⃣ Save cleaned extracted text
    extracted_path = EXTRACTED_DIR / f"{upload_path.stem}.txt"

    with open(extracted_path, "w", encoding="utf-8") as f:
        f.write(clean_text)

    # 5️⃣ Chunk CLEAN text
    chunks = chunk_text(clean_text)

    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="Text could not be chunked properly"
        )

    # 6️⃣ Store chunks in vector DB
    store_chunks(chunks, source=file.filename)

    return {
        "filename": file.filename,
        "characters_extracted": len(clean_text),
        "total_chunks": len(chunks),
        "status": "indexed"
    }



@app.post("/query")
def query_knowledge_base(question: str):
    # 1️⃣ Clean input (no assumptions)
    question = question.strip()

    # 2️⃣ Semantic search
    results = search_chunks(question)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        return {
            "question": question,
            "answer": "No relevant information found in the documents.",
            "sources": []
        }

    # 3️⃣ Debug (keep while tuning)
    print("Retrieved chunks:")
    for d, dist in zip(documents, distances):
        print(round(dist, 3), d[:120])

    # 4️⃣ Rank chunks by semantic relevance (LOWER = better)
    ranked = sorted(
        zip(documents, metadatas, distances),
        key=lambda x: x[2]
    )

    best_doc, best_meta, best_dist = ranked[0]

    # 5️⃣ Absolute relevance guard (GENERIC)
    # If everything is totally unrelated, do not hallucinate
    if best_dist > 1.4:
        return {
            "question": question,
            "answer": "This information is not available in the documents.",
            "sources": []
        }

    # 6️⃣ (Optional but recommended) include second-best chunk if close
    context_chunks = [best_doc]

    if len(ranked) > 1 and ranked[1][2] - best_dist < 0.15:
        context_chunks.append(ranked[1][0])

    print(context_chunks)
    # 7️⃣ Generate grounded answer
    answer = generate_answer(question, context_chunks)

    return {
        "question": question,
        "answer": answer,
        "sources": [
            {
                "source": best_meta.get("source"),
                "chunk_id": best_meta.get("chunk_id"),
                "distance": round(best_dist, 3)
            }
        ]
    }

@app.post("/query/retrieve-only")
def retrieve_only(question: str, top_k: int = 5):
    question = question.strip()

    results = search_chunks(question, top_k=top_k)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    if not documents:
        return {
            "question": question,
            "retrieved_chunks": [],
            "message": "No relevant chunks found"
        }

    retrieved = []

    for doc, meta, dist in zip(documents, metadatas, distances):
        retrieved.append({
            "content": doc,
            "source": meta.get("source"),
            "chunk_id": meta.get("chunk_id"),
            "distance": round(dist, 3)
        })

    return {
        "question": question,
        "top_k": top_k,
        "retrieved_chunks": retrieved
    }

@app.post("/query/evaluate")
def evaluate_retrieval(
    question: str,
    relevant_chunk_ids: list[int] = Query(...),
    top_k: int = 5
):
    results = search_chunks(question, top_k=top_k)

    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    retrieved_ids = [meta["chunk_id"] for meta in metadatas]

    precision = precision_at_k(retrieved_ids, relevant_chunk_ids)
    avg_dist = average_distance(distances)
    rec = recall(retrieved_ids, relevant_chunk_ids)

    return {
        "question": question,
        "precision_at_k": precision,
        "recall": rec,
        "average_distance": avg_dist,
        "retrieved_chunk_ids": retrieved_ids,
        "expected_relevant_chunk_ids": relevant_chunk_ids
    }
