import json

import numpy as np

from evaluation.metrics import abstention_rate, hit_at_k, reciprocal_rank, retrieval_summary
from evaluation.run_eval import DATASET_PATH, evaluate_retrieval, load_dataset


def test_hit_at_k():
    assert hit_at_k(["a", "b", "c"], "b", 1) == 0.0
    assert hit_at_k(["a", "b", "c"], "b", 2) == 1.0
    assert hit_at_k([], "b", 3) == 0.0


def test_reciprocal_rank():
    assert reciprocal_rank(["a", "b", "c"], "a") == 1.0
    assert reciprocal_rank(["a", "b", "c"], "c") == 1 / 3
    assert reciprocal_rank(["a", "b"], "x") == 0.0


def test_retrieval_summary_and_abstention():
    summary = retrieval_summary([(["a", "b"], "a"), (["x", "b"], "b")], k_values=(1, 2))
    assert summary["hit@1"] == 0.5
    assert summary["hit@2"] == 1.0
    assert summary["mrr"] == (1.0 + 0.5) / 2
    assert abstention_rate([0, 2, 0, 1]) == 0.5
    assert abstention_rate([]) == 0.0


def test_dataset_is_consistent():
    """Har bir savol mavjud hujjatga ishora qilishi va javobsiz savollarda hujjat ko'rsatilmasligi kerak."""
    data = load_dataset(DATASET_PATH)
    doc_ids = {d["id"] for d in data["documents"]}
    assert len(doc_ids) == len(data["documents"])
    for q in data["questions"]:
        if q["answerable"]:
            assert q["relevant_doc"] in doc_ids
            assert q["reference_answer"]
        else:
            assert q["relevant_doc"] is None


def test_evaluation_pipeline_with_fake_embedder():
    """
    Baholash kodining o'zi to'g'ri ishlashini tekshiradi (haqiqiy model yuklamasdan):
    so'z-xalta (bag-of-words) embedder bilan har bir savol o'z hujjatini topishi kerak.
    Bu modelning sifatini emas, faqat evaluation quvuri mantig'ini sinaydi.
    """
    data = load_dataset(DATASET_PATH)
    vocab = sorted({w.lower().strip(".,;?") for d in data["documents"] for w in d["text"].split()})
    index_of = {w: i for i, w in enumerate(vocab)}

    def embed(texts):
        vectors = np.zeros((len(texts), len(vocab)), dtype=np.float32)
        for row, text in enumerate(texts):
            for w in text.split():
                j = index_of.get(w.lower().strip(".,;?"))
                if j is not None:
                    vectors[row, j] += 1
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / np.where(norms == 0, 1, norms)

    summary, per_question, _ = evaluate_retrieval(
        data, embed, chunk_size=500, chunk_overlap=50, top_k=3, threshold=0.3
    )

    assert set(summary) >= {"hit@1", "hit@3", "mrr", "abstention_rate_unanswerable"}
    assert summary["hit@3"] >= 0.8
    assert len(per_question) == len(data["questions"])
    json.dumps(per_question)  # natija JSON'ga yozilishi mumkin bo'lishi kerak
