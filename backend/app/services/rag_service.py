"""RAG 检索与置信度判断。"""
from config import settings
from . import vector_store_service


def retrieve(query: str, scope_docs: list, k: int | None = None) -> list[dict]:
    if not scope_docs:
        return []
    k = k or settings.RETRIEVE_TOP_K
    items = vector_store_service.search(query, scope_docs, k)
    return [_normalize(i) for i in items]


def _normalize(item: dict) -> dict:
    return {
        "document_id": item.get("document_id"),
        "title": item.get("title", ""),
        "code": item.get("code", ""),
        "version": item.get("version", ""),
        "category": item.get("category", ""),
        "chapter": item.get("chapter", ""),
        "clause": item.get("clause", ""),
        "content": item.get("content", ""),
        "score": round(float(item.get("score", 0.0)), 4),
    }


def compute_low_confidence(items: list[dict]) -> bool:
    """无结果或最高相关度低于阈值时视为资料不足。"""
    if not items:
        return True
    best = max(i["score"] for i in items)
    return best < settings.RETRIEVE_MIN_SCORE
