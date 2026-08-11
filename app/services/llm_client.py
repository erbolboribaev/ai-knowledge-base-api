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


async def describe_image(base64_image: str, mime_type: str = "image/png") -> str:
    """
    Rasm/skrinshotni Groq vizual modeli orqali tavsiflaydi va undagi
    matnni (agar bo'lsa) ajratib oladi. Natija oddiy hujjat matni
    sifatida ishlatiladi - shu orqali skrinshot ham RAG tizimiga qo'shiladi.
    """
    client = get_groq_client()

    response = await client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Describe this image in detail and extract ALL visible text "
                            "exactly as written. If it's a screenshot of text/document, "
                            "transcribe the text fully and accurately. Respond with plain "
                            "text only - no markdown formatting."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{base64_image}"},
                    },
                ],
            }
        ],
        temperature=0.2,
        max_tokens=1024,
    )

    return response.choices[0].message.content.strip()
