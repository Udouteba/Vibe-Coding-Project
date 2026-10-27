"""文档管理：上传 / 解析 / 切分 / 索引 / 删除 / 重索引。"""

import asyncio
import os
import uuid
from pathlib import Path

from fastapi import UploadFile
from langchain_community.document_loaders import Docx2txtLoader, PyMuPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE, UPLOAD_DIR, settings

from ..common.exceptions import BusinessError
from ..database import SessionLocal
from ..models import Document, DocumentChunk
from ..utils.citation import extract_chapter, extract_clause
from . import vector_store_service

SEPARATORS = ["\n\n", "\n", "。", "；", "，", " ", ""]


def _splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=SEPARATORS,
    )


def _load_file(path: str):
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        return PyMuPDFLoader(path).load()
    if ext == ".docx":
        return Docx2txtLoader(path).load()
    return TextLoader(path, autodetect_encoding=True).load()


def _split_and_annotate(raw_docs) -> list[dict]:
    chunks = []
    for c in _splitter().split_documents(raw_docs):
        text = c.page_content.strip()
        if not text:
            continue
        chunks.append(
            {"content": text, "chapter": extract_chapter(text), "clause": extract_clause(text)}
        )
    return chunks


def _store_chunks(
    doc_id: int, title: str, code: str, version: str, category: str, chunks: list[dict]
) -> list[str]:
    texts = [c["content"] for c in chunks]
    ids = [uuid.uuid4().hex for _ in chunks]
    metadatas = [
        {
            "document_id": doc_id,
            "title": title,
            "code": code,
            "version": version,
            "category": category,
            "chapter": c["chapter"],
            "clause": c["clause"],
            "chunk_index": i,
        }
        for i, c in enumerate(chunks)
    ]
    vector_store_service.add_texts(category, texts, metadatas, ids)
    return ids


async def create_document(
    db: AsyncSession,
    title: str,
    code: str,
    version: str,
    category: str,
    file: UploadFile,
) -> Document:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise BusinessError(f"不支持的文件类型: {ext}，仅支持 {sorted(ALLOWED_EXTENSIONS)}")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise BusinessError("文件过大，最大支持 20MB")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}{ext}"
    save_path = os.path.join(UPLOAD_DIR, safe_name)
    with open(save_path, "wb") as f:
        f.write(content)

    doc = Document(
        title=title,
        code=code,
        version=version,
        category=category,
        status="pending",
        file_name=file.filename,
        file_path=save_path,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


async def index_document(doc_id: int) -> None:
    """解析 → 切分 → 向量化 → 入库；失败则标记 failed。"""
    async with SessionLocal() as db:
        doc = await db.get(Document, doc_id)
        if doc is None:
            return
        doc.status = "indexing"
        doc.error = ""
        await db.commit()
        file_path = doc.file_path
        category = doc.category
        title = doc.title
        code = doc.code
        version = doc.version

    try:
        raw_docs = await asyncio.to_thread(_load_file, file_path)
        chunks = await asyncio.to_thread(_split_and_annotate, raw_docs)
        if not chunks:
            raise BusinessError("文档解析后无有效内容")

        # 先清除旧向量（幂等，重索引安全）
        await asyncio.to_thread(vector_store_service.delete_document, category, doc_id)
        ids = await asyncio.to_thread(_store_chunks, doc_id, title, code, version, category, chunks)

        async with SessionLocal() as db:
            await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc_id))
            for i, c in enumerate(chunks):
                db.add(
                    DocumentChunk(
                        document_id=doc_id,
                        chunk_index=i,
                        content=c["content"],
                        chapter=c["chapter"],
                        clause=c["clause"],
                        vector_id=ids[i],
                    )
                )
            doc = await db.get(Document, doc_id)
            doc.status = "ready"
            doc.chunk_count = len(chunks)
            await db.commit()
    except Exception as e:
        async with SessionLocal() as db:
            doc = await db.get(Document, doc_id)
            doc.status = "failed"
            doc.error = str(e)
            await db.commit()
        raise BusinessError(f"索引失败: {e}") from e


async def delete_document(db: AsyncSession, doc_id: int) -> None:
    doc = await db.get(Document, doc_id)
    if doc is None:
        raise BusinessError("文档不存在", 404)
    category = doc.category
    file_path = doc.file_path

    await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == doc_id))
    await db.delete(doc)
    await db.commit()

    await asyncio.to_thread(vector_store_service.delete_document, category, doc_id)
    if file_path and os.path.exists(file_path):
        os.remove(file_path)


async def reindex_document(doc_id: int) -> None:
    await index_document(doc_id)


async def list_documents(db: AsyncSession) -> list[Document]:
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    return list(result.scalars().all())


async def list_chunks(db: AsyncSession, doc_id: int) -> list[DocumentChunk]:
    result = await db.execute(
        select(DocumentChunk)
        .where(DocumentChunk.document_id == doc_id)
        .order_by(DocumentChunk.chunk_index)
    )
    return list(result.scalars().all())


async def category_counts(db: AsyncSession) -> dict[str, int]:
    result = await db.execute(
        select(Document.category, func.count(Document.id)).group_by(Document.category)
    )
    return {cat: cnt for cat, cnt in result.all()}


async def load_scope_docs(db: AsyncSession, document_ids: list[int]) -> list[Document]:
    if document_ids:
        result = await db.execute(select(Document).where(Document.id.in_(document_ids)))
    else:
        result = await db.execute(select(Document).where(Document.status == "ready"))
    return list(result.scalars().all())
