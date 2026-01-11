import chromadb
from sentence_transformers import SentenceTransformer

# Initialize embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Initialize ChromaDB
chroma_client = chromadb.Client(
    settings=chromadb.Settings(
        persist_directory="data/vectordb"
    )
)

collection = chroma_client.get_or_create_collection(
    name="enterprise_documents"
)

def store_chunks(chunks: list[str], source: str):
    """
    Store text chunks with embeddings into ChromaDB.
    """
    embeddings = embedding_model.encode(chunks).tolist()

    ids = [f"{source}_{i}" for i in range(len(chunks))]
    metadatas = [{"source": source, "chunk_id": i} for i in range(len(chunks))]

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )


