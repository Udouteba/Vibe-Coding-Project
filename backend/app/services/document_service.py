"""文档管理：上传 / 解析 / 切分 / 索引 / 删除 / 重索引。"""

import asyncio
import json
import os
import sys
import time
import uuid
from pathlib import Path

import fitz  # pymupdf
from fastapi import UploadFile
from langchain_community.document_loaders import Docx2txtLoader, PyMuPDFLoader, TextLoader
from langchain_core.documents import Document as LCDocument
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from config import ALLOWED_EXTENSIONS, BASE_DIR, MAX_FILE_SIZE, UPLOAD_DIR, settings

from ..common.exceptions import BusinessError
from ..database import SessionLocal
from ..models import Document, DocumentChunk
from ..utils.citation import split_clauses
from . import vector_store_service


def _is_scanned_pdf(path: str) -> bool:
    """判断 PDF 是否无文字层（需走 OCR）。"""
    doc = fitz.open(path)
    try:
        return not any(page.get_text().strip() for page in doc)
    finally:
        doc.close()


def _pdf_page_count(path: str) -> int:
    doc = fitz.open(path)
    try:
        return len(doc)
    finally:
        doc.close()


def _ocr_jsonl_path(doc_id: int) -> str:
    return os.path.join(UPLOAD_DIR, f"{doc_id}.ocr.jsonl")


def _cleanup_ocr_jsonl(doc_id: int) -> None:
    path = _ocr_jsonl_path(doc_id)
    if os.path.exists(path):
        os.remove(path)


def _read_ocr_pages(jsonl_path: str) -> dict[int, str]:
    """读 OCR 中间文件，返回 {page_no: text}（容错跳过不完整/损坏行）。"""
    pages: dict[int, str] = {}
    if not os.path.exists(jsonl_path):
        return pages
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                pages[obj["page"]] = obj["text"]
            except (json.JSONDecodeError, KeyError, TypeError):
                continue
    return pages


async def _update_ocr_progress(doc_id: int, processed: int) -> None:
    async with SessionLocal() as db:
        doc = await db.get(Document, doc_id)
        if doc is not None:
            doc.processed_pages = processed
            await db.commit()


async def _run_ocr_batch(
    doc_id: int, file_path: str, jsonl_path: str, start: int, count: int
) -> bool:
    """启动一个 OCR 子进程处理 [start, start+count) 页，轮询进度，返回是否成功。"""
    cmd = [
        sys.executable,
        "-m",
        "app.ocr_worker",
        "--pdf",
        file_path,
        "--out",
        jsonl_path,
        "--start",
        str(start),
        "--count",
        str(count),
    ]
    for _ in range(settings.OCR_MAX_RETRY):
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(BASE_DIR),
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        deadline = time.monotonic() + settings.OCR_WORKER_TIMEOUT
        while proc.returncode is None:
            if time.monotonic() > deadline:
                proc.kill()
                break
            await asyncio.sleep(2)
            done = await asyncio.to_thread(_read_ocr_pages, jsonl_path)
            await _update_ocr_progress(doc_id, len(done))
        await proc.wait()
        if proc.returncode == 0:
            return True
    return False


async def _ocr_via_worker(file_path: str, doc_id: int) -> list[dict]:
    """扫描件 OCR：子进程分批 + 断点续传，返回 [{page, text}]（按页码排序）。"""
    total = await asyncio.to_thread(_pdf_page_count, file_path)
    jsonl_path = _ocr_jsonl_path(doc_id)
    done = await asyncio.to_thread(_read_ocr_pages, jsonl_path)

    async with SessionLocal() as db:
        doc = await db.get(Document, doc_id)
        if doc is not None:
            doc.total_pages = total
            doc.processed_pages = len(done)
            await db.commit()

    batch_size = settings.OCR_BATCH_SIZE
    if total <= settings.OCR_AUTO_SPLIT_THRESHOLD:
        batch_size = total  # 小文件单批一次跑完，只加载一次引擎

    remaining = [p for p in range(1, total + 1) if p not in done]
    while remaining:
        start = remaining[0]
        count = min(batch_size, remaining[-1] - start + 1)
        ok = await _run_ocr_batch(doc_id, file_path, jsonl_path, start, count)
        if not ok:
            raise BusinessError(f"OCR 子进程处理失败（第 {start} 页起 {count} 页，已重试）")
        done = await asyncio.to_thread(_read_ocr_pages, jsonl_path)
        remaining = [p for p in range(1, total + 1) if p not in done]

    return [{"page": p, "text": done[p]} for p in sorted(done)]


async def _parse_pdf(file_path: str, doc_id: int) -> list[LCDocument]:
    """解析 PDF：扫描件走子进程 OCR，文字层走 PyMuPDF。"""
    is_scanned = await asyncio.to_thread(_is_scanned_pdf, file_path)
    if is_scanned and settings.OCR_ENABLED:
        pages = await _ocr_via_worker(file_path, doc_id)
        return [
            LCDocument(page_content=p["text"], metadata={"page": p["page"]})
            for p in pages
        ]
    return await asyncio.to_thread(lambda: PyMuPDFLoader(file_path).load())


async def _parse_document(file_path: str, doc_id: int) -> list[LCDocument]:
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return await _parse_pdf(file_path, doc_id)
    if ext == ".docx":
        return await asyncio.to_thread(lambda: Docx2txtLoader(file_path).load())
    return await asyncio.to_thread(lambda: TextLoader(file_path, autodetect_encoding=True).load())


def _split_and_annotate(raw_docs) -> list[dict]:
    """语义条文切块：按「1.X.X 条文」切分，页码取每页序号（1-based）。"""
    pages = [{"page": i, "text": d.page_content} for i, d in enumerate(raw_docs, 1)]
    return split_clauses(pages, settings.CLAUSE_MAX_CHARS)


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
            "chapter": c.get("chapter", ""),
            "section": c.get("section", ""),
            "clause": c.get("clause", ""),
            "page": c.get("page", ""),
            "has_table": c.get("has_table", False),
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
        raise BusinessError("文件过大，最大支持 80MB")

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
        raw_docs = await _parse_document(file_path, doc_id)
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
                        chapter=c.get("chapter", ""),
                        section=c.get("section", ""),
                        clause=c.get("clause", ""),
                        page=c.get("page", ""),
                        vector_id=ids[i],
                    )
                )
            doc = await db.get(Document, doc_id)
            doc.status = "ready"
            doc.chunk_count = len(chunks)
            await db.commit()

        # 索引成功后才清理 OCR 中间文件（失败保留供断点续传）
        _cleanup_ocr_jsonl(doc_id)
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
    _cleanup_ocr_jsonl(doc_id)
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
