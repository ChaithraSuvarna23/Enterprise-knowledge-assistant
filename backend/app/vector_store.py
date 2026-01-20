import chromadb
from sentence_transformers import SentenceTransformer
from chromadb.config import Settings
from app.config import VECTOR_DB_DIR

# Initialize embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Initialize ChromaDB
chroma_client = chromadb.PersistentClient(
    path=str(VECTOR_DB_DIR),
    settings=Settings(anonymized_telemetry=False)
)

collection = chroma_client.get_or_create_collection(
    name="enterprise_documents"
)

def store_chunks(chunks: list[dict], source: str):
    texts = [c["text"] for c in chunks]

    embeddings = embedding_model.encode(texts).tolist()

    metadatas = []
    ids = []

    for idx, chunk in enumerate(chunks):
        ids.append(f"{source}_{idx}")

        metadatas.append({
            "chunk_id": idx,
            "source": source,
            "page": chunk["page"],   # ✅ PAGE NUMBER
            "chunk_size": len(chunk["text"])
        })

    # SAFETY CHECK — NEVER SKIP THIS
    assert len(texts) == len(embeddings) == len(metadatas) == len(ids)

    collection.add(
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )


def search_chunks(
    query: str,
    top_k: int = 8,
    min_distance: float = 1.1
):
    query_embedding = embedding_model.encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    dists = results["distances"][0]

    # 🔹 FILTER weak matches
    filtered = [
        (d, m, dist)
        for d, m, dist in zip(docs, metas, dists)
        if dist <= min_distance
    ]

    if not filtered:
        return {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]]
        }

    f_docs, f_metas, f_dists = zip(*filtered)

    return {
        "documents": [list(f_docs)],
        "metadatas": [list(f_metas)],
        "distances": [list(f_dists)]
    }


