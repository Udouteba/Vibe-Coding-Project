from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database import Base


class Document(Base):
    """给排水设计规范文档（原始文件 + 索引状态）。"""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    code: Mapped[str] = mapped_column(String(128), default="")
    version: Mapped[str] = mapped_column(String(64), default="")  # 版本 / 年份
    category: Mapped[str] = mapped_column(String(64), index=True, default="其他")
    status: Mapped[str] = mapped_column(
        String(32), default="pending"
    )  # pending/indexing/ready/failed
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    file_name: Mapped[str] = mapped_column(String(255), default="")
    file_path: Mapped[str] = mapped_column(String(512), default="")
    error: Mapped[str] = mapped_column(String(1024), default="")
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    """文档切分后的分片，保留章节/条款号，便于溯源与重建索引。"""

    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    chapter: Mapped[str] = mapped_column(String(128), default="")
    clause: Mapped[str] = mapped_column(String(128), default="")
    vector_id: Mapped[str] = mapped_column(String(128), default="")

    document = relationship("Document", back_populates="chunks")
