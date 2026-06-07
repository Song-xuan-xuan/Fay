import logging
import os
import re
import sys
import threading
from typing import Any, Dict, List, Optional

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    import utils.config_util as cfg

    CONFIG_UTIL_AVAILABLE = True
except ImportError:
    cfg = None
    CONFIG_UTIL_AVAILABLE = False

from utils.local_embedding_backend import (
    LocalEmbeddingBackend,
    is_local_backend,
    resolve_model_path,
)
from utils.openai_embedding_backend import OpenAIEmbeddingBackend

logger = logging.getLogger(__name__)


def _sanitize_text(text: str) -> str:
    if not isinstance(text, str) or not text:
        return text
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
    cleaned = re.sub(r"</?think>", "", cleaned, flags=re.IGNORECASE)
    return cleaned


def _config_value(name: str, fallback: Optional[str] = None) -> Optional[str]:
    if CONFIG_UTIL_AVAILABLE and cfg:
        try:
            if cfg.config is None:
                cfg.load_config()
            return getattr(cfg, name, fallback)
        except Exception as exc:
            logger.warning("读取 embedding 配置失败: %s", exc)
    return fallback


def _load_embedding_config() -> Dict[str, Optional[str]]:
    api_base_url = _config_value("embedding_api_base_url") or os.getenv("EMBEDDING_API_BASE_URL")
    api_key = _config_value("embedding_api_key") or os.getenv("EMBEDDING_API_KEY")
    model_name = (
        _config_value("embedding_api_model")
        or os.getenv("EMBEDDING_MODEL_PATH")
        or os.getenv("EMBEDDING_API_MODEL")
    )
    return {
        "api_base_url": api_base_url,
        "api_key": api_key,
        "model_name": model_name,
    }


class ApiEmbeddingService:
    """Embedding service with local model and OpenAI-compatible API backends."""

    _instance = None
    _lock = threading.Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._initialize_backend()
                    ApiEmbeddingService._initialized = True

    def _initialize_backend(self) -> None:
        config = _load_embedding_config()
        api_base_url = config["api_base_url"]
        api_key = config["api_key"]
        model_name = config["model_name"]

        if is_local_backend(api_base_url, model_name, project_root):
            self.backend = self._create_local_backend(model_name)
        else:
            self.backend = self._create_api_backend(api_base_url, api_key, model_name)

        self._sync_public_attrs()
        logger.info("Embedding 服务初始化完成: %s", self.get_model_info())

    def _create_local_backend(self, model_name: Optional[str]) -> LocalEmbeddingBackend:
        model_path = os.getenv("EMBEDDING_MODEL_PATH") or resolve_model_path(model_name, project_root)
        if not model_path:
            raise ValueError(
                "未配置本地 embedding 模型路径，请设置 "
                "embedding_api_model=model/bge-large-zh-v1.5 或 EMBEDDING_MODEL_PATH"
            )
        return LocalEmbeddingBackend(model_name or model_path, model_path)

    def _create_api_backend(
        self,
        api_base_url: Optional[str],
        api_key: Optional[str],
        model_name: Optional[str],
    ) -> OpenAIEmbeddingBackend:
        if not api_base_url:
            raise ValueError("未配置 embedding_api_base_url，请配置 gpt_base_url 或 EMBEDDING_API_BASE_URL")
        if not api_key:
            raise ValueError("未配置 embedding_api_key，请配置 gpt_api_key 或 EMBEDDING_API_KEY")
        model = model_name or os.getenv("EMBEDDING_API_MODEL", "text-embedding-ada-002")
        return OpenAIEmbeddingBackend(api_base_url, api_key, model)

    def _sync_public_attrs(self) -> None:
        info = self.backend.get_info()
        self.model_name = info["model_name"]
        self.embedding_dim = info["embedding_dim"]
        self.api_base_url = info["api_base_url"]
        self.local_model_path = info["local_model_path"]
        self.local_device = info["local_device"]
        self.service_type = info["service_type"]

    def encode_text(self, text: str) -> List[float]:
        result = self.backend.encode_text(_sanitize_text(text))
        self._sync_public_attrs()
        return result

    def encode_texts(self, texts: List[str]) -> List[List[float]]:
        cleaned = [_sanitize_text(text) for text in texts]
        result = self.backend.encode_texts(cleaned)
        self._sync_public_attrs()
        return result

    def get_model_info(self) -> dict:
        info = dict(self.backend.get_info())
        info["initialized"] = self._initialized
        return info

    def health_check(self) -> dict:
        try:
            embedding = self.encode_text("health_check")
            return {
                "status": "healthy",
                "test_successful": True,
                "embedding_dim": len(embedding) if embedding else None,
                **self.get_model_info(),
            }
        except Exception as exc:
            return {
                "status": "unhealthy",
                "test_successful": False,
                "error": str(exc),
                "service_type": getattr(self, "service_type", "unknown"),
            }


_global_embedding_service = None


def get_embedding_service() -> ApiEmbeddingService:
    global _global_embedding_service
    if _global_embedding_service is None:
        _global_embedding_service = ApiEmbeddingService()
    return _global_embedding_service


def _normalize_embedding_inputs(value: Any) -> List[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value]
    raise ValueError("Embedding input must be a string or a list of strings")


def build_openai_embedding_response(
    payload: Dict[str, Any],
    service: Optional[ApiEmbeddingService] = None,
) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ValueError("Embedding request body must be a JSON object")
    texts = _normalize_embedding_inputs(payload.get("input", ""))
    embedder = service or get_embedding_service()
    embeddings = embedder.encode_texts(texts)
    model_name = getattr(embedder, "model_name", None) or payload.get("model") or "embedding"
    return {
        "object": "list",
        "data": [
            {"object": "embedding", "embedding": embedding, "index": index}
            for index, embedding in enumerate(embeddings)
        ],
        "model": model_name,
        "usage": {"prompt_tokens": 0, "total_tokens": 0},
    }
