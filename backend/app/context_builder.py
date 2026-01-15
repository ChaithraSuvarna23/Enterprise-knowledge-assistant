# app/context_builder.py

def estimate_tokens(text: str) -> int:
    """
    Rough token estimation.
    1 token ≈ 4 characters (safe heuristic)
    """
    return max(1, len(text) // 4)


def build_context(
    chunks: list[str],
    max_tokens: int = 1500
) -> str:
    """
    Builds a clean, bounded context from retrieved chunks.
    """

    context_parts = []
    token_count = 0

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        tokens = estimate_tokens(chunk)

        if token_count + tokens > max_tokens:
            break

        context_parts.append(chunk)
        token_count += tokens

    return "\n\n".join(context_parts)
