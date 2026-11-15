"""
RAG sifatini baholash.

Ishga tushirish (loyiha ildizidan):
    python -m evaluation.run_eval                # faqat retrieval (tez, API kalitsiz)
    python -m evaluation.run_eval --answers      # + LLM javoblari va LLM-hakam (GROQ_API_KEY kerak)
    python -m evaluation.run_eval --chunk-size 60 --top-k 3 --json-out evaluation/results.json

Nimani o'lchaydi:
  1. Retrieval: Hit@1, Hit@3, MRR - kutilgan hujjat topildimi va qaysi o'rinda.
  2. Abstention: bazada javobi yo'q savollarda tizim kontekst topmadimi
     (production'dagi MIN_SIMILARITY_THRESHOLD bilan bir xil mantiq).
  3. (ixtiyoriy) Javob to'g'riligi: LLM javob generatsiya qiladi, boshqa chaqiruv
     (LLM-hakam) uni etalon javob bilan solishtiradi.

Eslatma: retrieval xotirada (numpy) hisoblanadi - production'dagi bo'laklash va
embedding modeli bilan bir xil, lekin pgvector so'rovini emas, kosinus o'xshashlikni
o'lchaydi. Baza chunk'larni bir xil metrika (cosine) bilan tartiblaydi.
"""
import argparse
import asyncio
import json
import os
from pathlib import Path

import numpy as np

from app.services.document_service import split_text_into_chunks
from evaluation.metrics import abstention_rate, retrieval_summary

DATASET_PATH = Path(__file__).parent / "dataset.json"
DEFAULT_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
NO_INFO_MESSAGE = "Sizda hali hujjat yuklanmagan yoki mos ma'lumot topilmadi."


def load_dataset(path: Path = DATASET_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_index(documents: list[dict], embed, chunk_size: int, chunk_overlap: int):
    """Hujjatlarni production'dagi kabi bo'laklarga bo'lib, embedding yaratadi."""
    chunk_texts: list[str] = []
    chunk_doc_ids: list[str] = []
    for doc in documents:
        for chunk in split_text_into_chunks(doc["text"], chunk_size, chunk_overlap):
            chunk_texts.append(chunk)
            chunk_doc_ids.append(doc["id"])
    vectors = np.asarray(embed(chunk_texts), dtype=np.float32)
    return chunk_texts, chunk_doc_ids, vectors


def retrieve(question: str, embed, index, top_k: int, threshold: float):
    """
    Savolga eng yaqin top_k ta bo'lak. Natija: [(doc_id, similarity, chunk_text)].
    Embedding'lar normallashtirilgan, shuning uchun nuqtaviy ko'paytma = kosinus o'xshashlik.
    Pastki chegaradan (threshold) past o'xshashlikdagilar tashlab yuboriladi.
    """
    chunk_texts, chunk_doc_ids, vectors = index
    query = np.asarray(embed([question]), dtype=np.float32)[0]
    similarities = vectors @ query
    order = np.argsort(-similarities)[:top_k]
    return [
        (chunk_doc_ids[i], float(similarities[i]), chunk_texts[i])
        for i in order
        if similarities[i] >= threshold
    ]


def unique_doc_order(hits) -> list[str]:
    """Bo'laklar ro'yxatidan hujjat id'larini birinchi uchrashuv tartibida, takrorlarsiz oladi."""
    seen: list[str] = []
    for doc_id, _, _ in hits:
        if doc_id not in seen:
            seen.append(doc_id)
    return seen


def evaluate_retrieval(dataset, embed, chunk_size, chunk_overlap, top_k, threshold):
    index = build_index(dataset["documents"], embed, chunk_size, chunk_overlap)
    answerable_results = []
    unanswerable_counts = []
    per_question = []

    for item in dataset["questions"]:
        # Hit@k/MRR uchun chegarasiz tartib kerak (threshold=-1), abstention uchun esa chegara bilan
        ranked = unique_doc_order(retrieve(item["question"], embed, index, top_k, threshold=-1.0))
        with_threshold = retrieve(item["question"], embed, index, top_k, threshold)

        if item["answerable"]:
            answerable_results.append((ranked, item["relevant_doc"]))
            per_question.append(
                {
                    "question": item["question"],
                    "expected": item["relevant_doc"],
                    "retrieved": ranked,
                    "hit": item["relevant_doc"] in ranked[:top_k],
                }
            )
        else:
            unanswerable_counts.append(len(with_threshold))
            per_question.append(
                {
                    "question": item["question"],
                    "expected": None,
                    "chunks_above_threshold": len(with_threshold),
                }
            )

    summary = retrieval_summary(answerable_results, k_values=(1, top_k) if top_k != 1 else (1,))
    summary["abstention_rate_unanswerable"] = abstention_rate(unanswerable_counts)
    return summary, per_question, index


async def judge_answer(client, model: str, question: str, reference: str, answer: str) -> bool:
    """LLM-hakam: javob etalon javobga mazmunan mos keladimi (ha/yo'q)."""
    prompt = (
        "You are grading an answer from a question-answering system.\n"
        f"Question: {question}\n"
        f"Reference answer: {reference}\n"
        f"System answer: {answer}\n\n"
        "Does the system answer contain the key facts of the reference answer without "
        "contradicting it? Reply with exactly one word: YES or NO."
    )
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=3,
    )
    return response.choices[0].message.content.strip().upper().startswith("YES")


async def evaluate_answers(dataset, embed, index, top_k, threshold):
    # Faqat shu rejimda kerak bo'ladi, shuning uchun lazy import (kalitsiz retrieval ishlayversin)
    from app.core.config import settings
    from app.services.llm_client import generate_answer, get_groq_client

    client = get_groq_client()
    correct = 0
    answerable_total = 0
    abstained = 0
    unanswerable_total = 0
    details = []

    for item in dataset["questions"]:
        hits = retrieve(item["question"], embed, index, top_k, threshold)
        if hits:
            answer = await generate_answer(item["question"], [text for _, _, text in hits])
        else:
            answer = NO_INFO_MESSAGE  # rag_service ham shunday qiladi - LLM chaqirilmaydi

        if item["answerable"]:
            answerable_total += 1
            ok = await judge_answer(
                client, settings.llm_model, item["question"], item["reference_answer"], answer
            )
            correct += ok
            details.append({"question": item["question"], "correct": ok, "answer": answer})
        else:
            unanswerable_total += 1
            declined = (not hits) or any(
                phrase in answer.lower() for phrase in ("topa olmadim", "ma'lumot yo'q", "don't have")
            )
            abstained += declined
            details.append({"question": item["question"], "abstained": declined, "answer": answer})

    return {
        "answer_accuracy": correct / answerable_total if answerable_total else 0.0,
        "abstention_after_generation": abstained / unanswerable_total if unanswerable_total else 0.0,
    }, details


def get_embedder(model_name: str):
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)
    return lambda texts: model.encode(texts, normalize_embeddings=True)


def main():
    parser = argparse.ArgumentParser(description="Evaluate the RAG pipeline")
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument("--chunk-overlap", type=int, default=50)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--threshold", type=float, default=0.3, help="Keep in sync with MIN_SIMILARITY_THRESHOLD")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--answers", action="store_true", help="Also generate answers and judge them with the LLM")
    parser.add_argument("--json-out", type=Path, default=None)
    args = parser.parse_args()

    dataset = load_dataset()
    embed = get_embedder(args.model)

    summary, per_question, index = evaluate_retrieval(
        dataset, embed, args.chunk_size, args.chunk_overlap, args.top_k, args.threshold
    )
    report = {"config": vars(args) | {"json_out": None}, "retrieval": summary, "per_question": per_question}

    if args.answers:
        answer_summary, answer_details = asyncio.run(
            evaluate_answers(dataset, embed, index, args.top_k, args.threshold)
        )
        report["answers"] = answer_summary
        report["answer_details"] = answer_details

    print(f"\nModel: {args.model} | chunk_size={args.chunk_size} | top_k={args.top_k}")
    for name, value in report["retrieval"].items():
        print(f"  {name:32s} {value:.3f}")
    for name, value in report.get("answers", {}).items():
        print(f"  {name:32s} {value:.3f}")
    misses = [q for q in per_question if q.get("expected") and not q["hit"]]
    if misses:
        print("\nMissed questions:")
        for q in misses:
            print(f"  - {q['question']} (expected {q['expected']}, got {q['retrieved']})")

    if args.json_out:
        args.json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
