import re

def keyword_overlap_score(text: str, question: str) -> int:
    text = text.lower()
    question = question.lower()

    keywords = re.findall(r"\w+", question)
    return sum(1 for k in keywords if k in text)


def rerank_chunks(documents, metadatas, distances, question):
    reranked = []

    for doc, meta, dist in zip(documents, metadatas, distances):
        score = keyword_overlap_score(doc, question)

        # EXACT tuple shape (4 values only)
        reranked.append((score, doc, meta, dist))

    # Higher keyword score is better
    reranked.sort(key=lambda x: x[0], reverse=True)

    return reranked
