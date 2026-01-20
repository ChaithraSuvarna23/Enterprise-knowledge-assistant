# app/answerability.py

import re

def extract_keywords(question: str) -> list[str]:
    # simple keyword extractor (rule-based)
    words = re.findall(r"\b[a-zA-Z]{3,}\b", question.lower())
    stopwords = {
        "what", "when", "where", "which", "that", "this",
        "with", "from", "have", "will", "does", "how"
    }
    return [w for w in words if w not in stopwords]


def is_answerable(chunks: list[str], question: str) -> bool:
    q = question.lower().strip()

    # ✅ Allow section-style questions
    if len(q.split()) <= 4:
        return True

    keywords = extract_keywords(question)

    hits = 0
    for chunk in chunks:
        chunk_lower = chunk.lower()
        if any(k in chunk_lower for k in keywords):
            hits += 1

    return hits >= 1
