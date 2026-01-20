from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
EXTRACTED_DIR = DATA_DIR / "extracted"
VECTOR_DB_DIR = DATA_DIR / "vectordb"   

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True) 

CHUNK_SIZE = 400
CHUNK_OVERLAP = 80

API_KEY = os.getenv("GROQ_API_KEYY")
GROQ_MODEL = "llama-3.1-8b-instant"