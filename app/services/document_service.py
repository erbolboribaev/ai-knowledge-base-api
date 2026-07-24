import re


def split_text_into_chunks(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> list[str]:
    """
    Uzun matnni kichik bo'laklarga bo'ladi - RAG uchun zarur, chunki
    LLM'ga butun hujjatni emas, faqat savolga eng mos bo'lgan
    bo'lakni yuboramiz.

    chunk_overlap - qo'shni bo'laklar orasida bir oz matn takrorlanadi,
    shunda gap o'rtasida kesilib, ma'no yo'qolib qolmaydi.

    Bo'lish so'zlar chegarasida amalga oshiriladi (so'zni yarmida kesmaslik uchun).
    """
    # Ortiqcha bo'sh joylarni tozalash
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return []

    words = text.split(" ")
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))

        if end >= len(words):
            break

        # Keyingi bo'lak overlap miqdoricha orqaga qaytib boshlanadi
        start = end - chunk_overlap

    return chunks
