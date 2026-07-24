from groq import AsyncGroq
from app.core.config import settings

_client: AsyncGroq | None = None


def get_groq_client() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=settings.groq_api_key)
    return _client


async def generate_answer(question: str, context_chunks: list[str]) -> str:
    """
    Berilgan savol va topilgan hujjat bo'laklari (context) asosida
    LLM orqali javob generatsiya qiladi. Bu - RAG'ning "Generation" qismi.
    """
    client = get_groq_client()

    context_text = "\n\n---\n\n".join(context_chunks)

    prompt = f"""Siz kompaniya bilim bazasi bo'yicha yordamchisiz.
Quyidagi kontekst asosida foydalanuvchi savoliga javob bering.
Agar kontekstda javob topilmasa, "Kechirasiz, bu haqda ma'lumot topa olmadim" deb ayting.
Javobni faqat berilgan kontekst asosida bering, o'zingizdan qo'shmang.

Kontekst:
{context_text}

Savol: {question}

Javob:"""

    response = await client.chat.completions.create(
        messages=[
            {"role": "system", "content": "Siz aniq va foydali bilim bazasi yordamchisisiz."},
            {"role": "user", "content": prompt},
        ],
        model=settings.llm_model,
        temperature=0.2,
        max_tokens=800,
    )

    return response.choices[0].message.content.strip()
