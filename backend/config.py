"""全局配置：从 backend/.env 读取，导出若干常量。"""
import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore"
    )

    # 数据库
    DATABASE_URL: str = (
        "mysql+asyncmy://root:123456@127.0.0.1:3306/drainage?charset=utf8mb4"
    )

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

    # 文档切分
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 120

    # Agent
    AGENT_RECURSION_LIMIT: int = 10


settings = Settings()

# 在 huggingface_hub 读取前写入环境变量，确保 BGE 模型加载走国内镜像 + 离线
os.environ["HF_ENDPOINT"] = settings.HF_ENDPOINT
os.environ["HF_HUB_OFFLINE"] = settings.HF_HUB_OFFLINE
os.environ["TRANSFORMERS_OFFLINE"] = settings.HF_HUB_OFFLINE

# 上传相关常量
UPLOAD_DIR = str(BASE_DIR / "uploads")
VECTOR_DIR = settings.VECTOR_DIR
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB
ALLOWED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}

# 专业分类（给水 / 排水 / 消防 / 建筑给水排水 / 其他）
CATEGORIES = ["给水", "排水", "消防", "建筑给水排水", "其他"]
