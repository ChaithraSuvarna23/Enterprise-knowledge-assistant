from groq import Groq
from groq import RateLimitError
from app.config import API_KEY, GROQ_MODEL

# Create Groq client using env variable
client = Groq(api_key=API_KEY)


def generate_answer(question: str, context_chunks: list[str]) -> str:
    context_text = ""
    for i, chunk in enumerate(context_chunks, 1):
        context_text += f"[Context {i}]\n{chunk}\n\n"
        
    system_prompt = (
        "You are an enterprise knowledge assistant.\n"
    "You must answer strictly using the provided context.\n\n"

    "Rules:\n"
    "- Use ONLY facts from the context\n"
    "- Combine information from multiple context sections if needed\n"
    "- Answer in complete sentences\n"
    "- Be precise and detailed when the context allows\n"
    "- If the context does not fully answer the question, say:\n"
    "'This information is not fully available in the documents.'\n"
    )

    user_prompt = f"""
Context:
{context_text}

Question:
{question}

Answer:
"""

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,
            max_tokens=500,
        )

        return response.choices[0].message.content.strip()

    except RateLimitError:
        return "LLM rate limit exceeded. Please try again later."

    except Exception as e:
        # Safe fallback (important for enterprise systems)
        return "An error occurred while generating the answer."
