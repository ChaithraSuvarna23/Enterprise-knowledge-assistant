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

def store_chunks(chunks: list[str], source: str):
    embeddings = embedding_model.encode(chunks).tolist()

    ids = [f"{source}_{i}" for i in range(len(chunks))]
    metadatas = [{"source": source, "chunk_id": i} for i in range(len(chunks))]

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )
    

def search_chunks(query: str, top_k: int = 3):
    """
    Search for relevant document chunks using semantic similarity.
    """
    query_embedding = embedding_model.encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"]

    )

    return results

