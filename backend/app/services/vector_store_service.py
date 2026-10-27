"""向量库服务：ChromaDB 按专业分片（每专业一个 collection）+ 检索缓存。"""

import hashlib
import logging

from cachetools import TTLCache
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from config import settings

logger = logging.getLogger("drainage")

_embeddings: HuggingFaceEmbeddings | None = None
_stores: dict[str, Chroma] = {}
_cache: TTLCache = TTLCache(maxsize=settings.RETRIEVE_CACHE_MAX, ttl=settings.RETRIEVE_CACHE_TTL)

# Chroma 集合名仅支持 [a-zA-Z0-9._-]，分类为中文，需映射为 ASCII slug
_CATEGORY_SLUGS = {
    "给水": "water",
    "排水": "drainage",
    "消防": "fire",
    "建筑给水排水": "building",
    "其他": "other",
}


def _collection_name(category: str) -> str:
    slug = _CATEGORY_SLUGS.get(category)
    if slug is None:
        slug = hashlib.md5(category.encode("utf-8")).hexdigest()[:12]
    return f"{settings.VECTOR_COLLECTION_PREFIX}_{slug}"


def get_embeddings() -> HuggingFaceEmbeddings:
    global _embeddings
    if _embeddings is None:
        logger.info("加载本地 embedding 模型: %s", settings.EMBEDDING_MODEL_NAME)
        _embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL_NAME,
            model_kwargs={"device": settings.EMBEDDING_DEVICE},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings


def get_store(category: str) -> Chroma:
    if category not in _stores:
        _stores[category] = Chroma(
            collection_name=_collection_name(category),
            embedding_function=get_embeddings(),
            persist_directory=settings.VECTOR_DIR,
            collection_metadata={"hnsw:space": "cosine"},
        )
    return _stores[category]


def _cache_key(query: str, scope_docs: list, k: int) -> str:
    ids = sorted(d.id for d in scope_docs)
    return f"{query}|{ids}|{k}"


def add_texts(category: str, texts: list[str], metadatas: list[dict], ids: list[str]) -> None:
    store = get_store(category)
    store.add_texts(texts=texts, metadatas=metadatas, ids=ids)
    _cache.clear()


def delete_document(category: str, document_id: int) -> None:
    store = get_store(category)
    store.delete(where={"document_id": document_id})
    _cache.clear()


def search(query: str, scope_docs: list, k: int) -> list[dict]:
    """按专业分片检索：对各专业 collection 分别查询，再按相关度合并排序。"""
    if not scope_docs:
        return []

    by_cat: dict[str, list] = {}
    for d in scope_docs:
        by_cat.setdefault(d.category, []).append(d)

    key = _cache_key(query, scope_docs, k)
    cached = _cache.get(key)
    if cached is not None:
        return cached

    merged: list[dict] = []
    for cat, docs in by_cat.items():
        store = get_store(cat)
        ids = [d.id for d in docs]
        try:
            results = store.similarity_search_with_relevance_scores(
                query, k=k, filter={"document_id": {"$in": ids}}
            )
        except Exception as e:  # 空 collection 或过滤无结果时兜底
            logger.warning("检索 %s 失败: %s", cat, e)
            results = []
        for doc, score in results:
            meta = dict(doc.metadata)
            meta["content"] = doc.page_content
            meta["score"] = score
            merged.append(meta)

    merged.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    merged = merged[:k]
    _cache[key] = merged
    return merged
