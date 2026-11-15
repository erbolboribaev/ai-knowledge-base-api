"""RAG sifatini o'lchash uchun sof (pure) metrikalar - tashqi kutubxonasiz, oson testlanadi."""


def hit_at_k(ranked_doc_ids: list[str], relevant_doc_id: str, k: int) -> float:
    """Kutilgan hujjat dastlabki k ta natija orasida bormi (1.0 yoki 0.0)."""
    return 1.0 if relevant_doc_id in ranked_doc_ids[:k] else 0.0


def reciprocal_rank(ranked_doc_ids: list[str], relevant_doc_id: str) -> float:
    """Kutilgan hujjat birinchi marta uchragan o'rin bo'yicha 1/o'rin; umuman topilmasa 0."""
    for position, doc_id in enumerate(ranked_doc_ids, start=1):
        if doc_id == relevant_doc_id:
            return 1.0 / position
    return 0.0


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def retrieval_summary(
    results: list[tuple[list[str], str]], k_values: tuple[int, ...] = (1, 3)
) -> dict[str, float]:
    """
    results - har bir savol uchun (tartiblangan hujjat id'lari, kutilgan hujjat id) juftligi.
    Hit@k va MRR qaytaradi.
    """
    summary = {
        f"hit@{k}": mean([hit_at_k(ranked, expected, k) for ranked, expected in results])
        for k in k_values
    }
    summary["mrr"] = mean([reciprocal_rank(ranked, expected) for ranked, expected in results])
    return summary


def abstention_rate(retrieved_counts: list[int]) -> float:
    """
    Javobi bazada yo'q savollar uchun: nechta savolda tizim hech qanday
    kontekst topmadi (ya'ni to'g'ri "bilmayman" deyishga tayyor). Yuqori - yaxshi.
    """
    if not retrieved_counts:
        return 0.0
    return sum(1 for count in retrieved_counts if count == 0) / len(retrieved_counts)
