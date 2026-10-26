from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.response import ok
from ..database import get_db
from ..dependencies.auth import get_current_admin, get_current_user
from ..models import Document, User
from ..schemas.document import DocumentChunkOut, DocumentOut
from ..services import document_service

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
async def list_documents(
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    docs = await document_service.list_documents(db)
    return ok([DocumentOut.model_validate(d).model_dump() for d in docs])


@router.post("")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    code: str = Form(""),
    version: str = Form(""),
    category: str = Form("其他"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    doc = await document_service.create_document(db, title, code, version, category, file)
    await document_service.index_document(doc.id)
    fresh = await db.get(Document, doc.id)
    return ok(DocumentOut.model_validate(fresh).model_dump(), "上传并索引成功")


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    await document_service.delete_document(db, doc_id)
    return ok(message="删除成功")


@router.post("/{doc_id}/reindex")
async def reindex_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    await document_service.reindex_document(doc_id)
    fresh = await db.get(Document, doc_id)
    return ok(DocumentOut.model_validate(fresh).model_dump(), "重新索引成功")


@router.get("/{doc_id}/chunks")
async def list_chunks(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    chunks = await document_service.list_chunks(db, doc_id)
    return ok([DocumentChunkOut.model_validate(c).model_dump() for c in chunks])
