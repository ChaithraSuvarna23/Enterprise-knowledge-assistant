def precision_at_k(retrieved_chunks: list[str], relevant_chunks: list[str]) -> float:
    if not retrieved_chunks:
        return 0.0

    relevant_set = set(relevant_chunks)
    retrieved_set = set(retrieved_chunks)

    true_positives = len(retrieved_set & relevant_set)

    return round(true_positives / len(retrieved_set), 3)

def average_distance(distances: list[float]) -> float:
    if not distances:
        return 0.0
    return round(sum(distances) / len(distances), 3)

def recall(retrieved_chunks: list[str], relevant_chunks: list[str]) -> float:
    if not relevant_chunks:
        return 0.0

    relevant_set = set(relevant_chunks)
    retrieved_set = set(retrieved_chunks)

    return round(len(relevant_set & retrieved_set) / len(relevant_set), 3)
