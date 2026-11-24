"""全局配置：从 backend/.env 读取，导出若干常量。"""

import logging
import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Windows 下 torch（embedding）与 paddle（OCR）同进程，OpenMP 运行时重复加载会冲突，
# 需在 import paddle 前声明允许重复加载（paddle 在 ocr_service 内延迟 import）。
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    # 数据库
    DATABASE_URL: str = "mysql+asyncmy://root:123456@127.0.0.1:3306/drainage?charset=utf8mb4"

    # JWT
    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7

    # LLM（DeepSeek）
    LLM_BASE_URL: str = "https://api.deepseek.com"
    LLM_API_KEY: str = ""
    LLM_MODEL_NAME: str = "deepseek-chat"
    LLM_TEMPERATURE: float = 0.3

    # Embedding（本地 BGE 中文模型）
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-zh-v1.5"
    EMBEDDING_DEVICE: str = "cpu"
    # huggingface.co 在国内不可达，默认走 hf-mirror.com 镜像
    HF_ENDPOINT: str = "https://hf-mirror.com"
    # 模型已缓存时走离线加载，避免网络抖动导致卡顿；首次下载模型需临时设为 0
    HF_HUB_OFFLINE: str = "1"

    # 向量库
    VECTOR_DIR: str = str(BASE_DIR / "data" / "chroma")
    VECTOR_COLLECTION_PREFIX: str = "drainage"

    # 检索
    RETRIEVE_TOP_K: int = 6
    RETRIEVE_MIN_SCORE: float = 0.25
    RETRIEVE_CACHE_TTL: int = 300
    RETRIEVE_CACHE_MAX: int = 512

    # Rerank 重排（bi-encoder 粗召回 N 条 → cross-encoder 精排取 TOP_K）
    RERANK_ENABLED: bool = True
    RERANK_MODEL_NAME: str = "BAAI/bge-reranker-base"
    RERANK_RECALL_N: int = 20
    RERANK_MAX_LENGTH: int = 512

    # 文档切分
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 120
    CLAUSE_MAX_CHARS: int = 500  # 条文语义切块：单条超过此长度二次切分（overlap=0）

    # OCR（扫描件：无文字层 PDF 走 PaddleOCR / PP-Structure）
    OCR_ENABLED: bool = True          # 无文字层时是否走 OCR
    OCR_USE_TABLE: bool = True        # 是否启用 PP-Structure 表格识别
    OCR_DPI: int = 120                # 渲染 PDF 页为图的分辨率（Windows CPU 大图触发 paddle 卷积核崩溃，控制在 120dpi）
    OCR_MAX_SIDE: int = 1400          # 渲染图最大边长，超出等比缩小（规避 paddle CPU segfault）
    OCR_WM_THRESHOLD: int = 200       # 浅灰白化阈值：灰度≥此值视为水印→置白
    OCR_WM_WORDS: str = "住房城乡建设部,信息公开,浏览专用"  # 水印黑名单（逗号分隔独立词）
    OCR_MODEL_DIR: str = ""           # 为空走默认下载；可指向离线模型目录

    # 分批 OCR（大文件：子进程分批 + 断点续传，隔离 paddle 与 torch 的 OpenMP 冲突）
    OCR_BATCH_SIZE: int = 20            # 每批处理页数
    OCR_AUTO_SPLIT_THRESHOLD: int = 30  # 总页数超过此值才分批（≤ 则单批一次跑完）
    OCR_WORKER_TIMEOUT: int = 1800      # 单批子进程超时（秒），默认 30 分钟
    OCR_MAX_RETRY: int = 2              # 单批失败/超时的重试次数

    # Agent
    AGENT_RECURSION_LIMIT: int = 10


settings = Settings()

if settings.JWT_SECRET_KEY == "change-me":
    logging.getLogger("drainage").warning(
        "JWT_SECRET_KEY 仍为默认值 'change-me'，请在生产环境通过 .env 覆盖"
    )

# 在 huggingface_hub 读取前写入环境变量，确保 BGE 模型加载走国内镜像 + 离线
os.environ["HF_ENDPOINT"] = settings.HF_ENDPOINT
os.environ["HF_HUB_OFFLINE"] = settings.HF_HUB_OFFLINE
os.environ["TRANSFORMERS_OFFLINE"] = settings.HF_HUB_OFFLINE

# 上传相关常量
UPLOAD_DIR = str(BASE_DIR / "uploads")
VECTOR_DIR = settings.VECTOR_DIR
MAX_FILE_SIZE = 80 * 1024 * 1024  # 80MB
ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}

# 专业分类（给水 / 排水 / 消防 / 建筑给水排水 / 其他）
CATEGORIES = ["给水", "排水", "消防", "建筑给水排水", "其他"]
