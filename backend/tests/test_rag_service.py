"""RAG 检索与置信度判断（mock 向量检索）。"""

from app.services import rag_service, vector_store_service


def test_retrieve_empty_scope():
    assert rag_service.retrieve("问题", []) == []


def test_retrieve_normalizes(monkeypatch):
    monkeypatch.setattr(
        vector_store_service,
        "search",
        lambda query, docs, k: [
            {
                "document_id": 1,
                "title": "规范",
                "code": "GB",
                "version": "2019",
                "category": "给水",
                "chapter": "第一章",
                "clause": "1.1",
                "content": "内容",
                "score": 0.9,
            }
        ],
    )
    items = rag_service.retrieve("问题", [object()], k=1)
    assert items[0]["document_id"] == 1
    assert items[0]["score"] == 0.9


def test_compute_low_confidence_empty():
    assert rag_service.compute_low_confidence([]) is True


def test_compute_low_confidence_below_threshold():
    assert rag_service.compute_low_confidence([{"score": 0.1}]) is True


def test_compute_low_confidence_above_threshold():
    assert rag_service.compute_low_confidence([{"score": 0.9}]) is False
