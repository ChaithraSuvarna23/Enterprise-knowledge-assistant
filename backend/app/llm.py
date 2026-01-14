from openai import OpenAI
from openai import RateLimitError
from app.config import OPENAI_API_KEY, OPENAI_MODEL

client = OpenAI(api_key=OPENAI_API_KEY)

def generate_answer(question: str, context_chunks: list[str]) -> str:
    context = "\n\n".join(context_chunks)

    system_prompt = (
        "You are an enterprise knowledge assistant.\n"
        "Answer ONLY using the provided context.\n"
        "If the answer is not present, say:\n"
        "'This information is not available in the documents.'"
    )

    user_prompt = f"""
Context:
{context}

Question:
{question}

Answer:
"""

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            max_tokens=150
        )

        return response.choices[0].message.content.strip()

    except RateLimitError:
        return "LLM quota exceeded. Please try again later."
