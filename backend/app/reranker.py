import re

def keyword_overlap_score(text: str, question: str) -> int:
    text = text.lower()
    question = question.lower()

    keywords = re.findall(r"\w+", question)
    return sum(1 for k in keywords if k in text)


def rerank_chunks(documents, metadatas, distances, question):
    reranked = []

    q = question.lower()

    for doc, meta, dist in zip(documents, metadatas, distances):
        keyword_score = keyword_overlap_score(doc, question)

        # ✅ Heading boost
        heading_boost = 0
        if q in doc.lower()[:200]:
            heading_boost = 2

        final_score = keyword_score + heading_boost - dist

        reranked.append((final_score, doc, meta, dist))

    reranked.sort(key=lambda x: x[0], reverse=True)
    return reranked

