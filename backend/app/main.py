from fastapi import FastAPI, UploadFile, File, HTTPException
from pathlib import Path
import shutil
import uuid
from app.llm import generate_answer
from app.evaluation import precision_at_k, average_distance,recall
from fastapi import Query



from app.config import UPLOAD_DIR, EXTRACTED_DIR
from app.utils import extract_pages_from_pdf, extract_text_from_txt,chunk_text
from app.vector_store import store_chunks, search_chunks
from app.context_builder import build_context
from app.reranker import rerank_chunks


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
    Upload a PDF or TXT document, extract text,
    chunk it with page numbers, and store embeddings.
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

    # 2️⃣ Extract + chunk
    if file_ext == ".pdf":
        # PDF → pages → chunks (with page numbers)
        pages = extract_pages_from_pdf(upload_path)
        chunks = chunk_text(pages)

    else:
        # TXT → single page → chunks
        extracted_text = extract_text_from_txt(upload_path)

        if not extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail="No readable text found in TXT file"
            )

        clean_text = (
            extracted_text
            .encode("utf-8", errors="ignore")
            .decode("utf-8")
        )

        pages = [{
            "page": 1,
            "text": clean_text
        }]

        chunks = chunk_text(pages)

    if not chunks:
        raise HTTPException(
            status_code=400,
            detail="Text could not be chunked properly"
        )

    # 3️⃣ Store chunks in vector DB
    store_chunks(chunks, source=file.filename)

    return {
        "filename": file.filename,
        "total_chunks": len(chunks),
        "status": "indexed"
    }



@app.post("/query")
def query_knowledge_base(question: str):
    question = question.strip()

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

    # 1️⃣ Initial semantic ranking
    ranked = sorted(
        zip(documents, metadatas, distances),
        key=lambda x: x[2]
    )

    # 2️⃣ Take top-N semantic candidates
    top_docs = [r[0] for r in ranked[:5]]
    top_metas = [r[1] for r in ranked[:5]]
    top_dists = [r[2] for r in ranked[:5]]

    # 3️⃣ RERANK (keyword-based)
    reranked = rerank_chunks(
        top_docs,
        top_metas,
        top_dists,
        question
    )

    # 4️⃣ SAFE UNPACK (NOW MATCHES)
    best_score, best_doc, best_meta, best_dist = reranked[0]

    # 5️⃣ Absolute relevance guard
    if best_dist > 1.4:
        return {
            "question": question,
            "answer": "This information is not available in the documents.",
            "sources": []
        }

    # 6️⃣ Context builder
    context = build_context([best_doc], max_tokens=1200)

    answer = generate_answer(question, [context])
    
    return {
        "question": question,
        "answer": answer,
        "sources": [
            {
                "source": best_meta.get("source"),
                "chunk_id": best_meta.get("chunk_id"),
                "page": best_meta.get("page"),
                "distance": round(best_dist, 3)
            }
        ]
    }





@app.post("/query/retrieve-only")
def retrieve_only(
    question: str,
    top_k: int = 5,
    min_distance: float = 1.1,
    source: str | None = None
):
    question = question.strip()

    results = search_chunks(
        query=question,
        top_k=top_k,
        min_distance=min_distance
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    context_preview = build_context(documents, max_tokens=800)


    return {
        "question": question,
        "results": [
            {
                "chunk_id": meta["chunk_id"],
                "source": meta["source"],
                "page": meta["page"],
                "distance": round(dist, 3),
                "text": doc
            }
            for doc, meta, dist in zip(documents, metadatas, distances)
        ]
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
