import logging
import os
import threading
from typing import List, Optional

logger = logging.getLogger(__name__)

LOCAL_BACKEND_VALUES = {"local", "local_model", "sentence_transformer", "sentence-transformer"}


def resolve_model_path(
    model_name: Optional[str],
    project_root: str,
    must_exist: bool = False,
) -> Optional[str]:
    model_value = str(model_name or "").strip()
    if not model_value:
        return None
    expanded = os.path.expandvars(os.path.expanduser(model_value))
    candidates = [expanded]
    if not os.path.isabs(expanded):
        candidates.append(os.path.join(project_root, expanded))
    for candidate in candidates:
        if os.path.exists(candidate):
            return os.path.abspath(candidate)
    return None if must_exist else expanded


def is_local_backend(
    base_url: Optional[str],
    model_name: Optional[str],
    project_root: str,
) -> bool:
    base_value = str(base_url or "").strip().lower()
    if base_value in LOCAL_BACKEND_VALUES:
        return True
    if base_value:
        return False
    return bool(resolve_model_path(model_name, project_root, must_exist=True))


def _select_device() -> str:
    configured = os.getenv("EMBEDDING_DEVICE")
    if configured:
        return configured
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def _to_float_list(value) -> List[float]:
    if hasattr(value, "tolist"):
        value = value.tolist()
    if isinstance(value, tuple):
        value = list(value)
    return [float(item) for item in value]


class TransformersEmbeddingModel:
    """Fallback encoder when sentence_transformers cannot be imported."""

    def __init__(self, model_path: str, device: str):
        import torch
        from transformers import AutoModel, AutoTokenizer

        self.torch = torch
        self.device = device
        self.max_length = int(os.getenv("EMBEDDING_MAX_LENGTH", "512"))
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModel.from_pretrained(model_path)
        self.model.to(device)
        self.model.eval()

    def encode(self, texts: List[str], normalize_embeddings: bool = True):
        if isinstance(texts, str):
            texts = [texts]
        encoded = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )
        encoded = {key: value.to(self.device) for key, value in encoded.items()}
        with self.torch.no_grad():
            outputs = self.model(**encoded)
            vectors = outputs.last_hidden_state[:, 0]
            if normalize_embeddings:
                vectors = self.torch.nn.functional.normalize(vectors, p=2, dim=1)
        return vectors.cpu().tolist()


class LocalEmbeddingBackend:
    def __init__(self, model_name: str, model_path: str):
        self.model_name = model_name or model_path
        self.model_path = model_path
        self.device = _select_device()
        self.embedding_dim = None
        self._model = None
        self._lock = threading.Lock()

    def _load_model(self):
        if self._model is None:
            with self._lock:
                if self._model is None:
                    try:
                        from sentence_transformers import SentenceTransformer

                        logger.info("正在加载本地 embedding 模型: %s", self.model_path)
                        self._model = SentenceTransformer(self.model_path, device=self.device)
                    except ImportError as exc:
                        logger.warning("SentenceTransformer 加载失败，改用 transformers 兜底: %s", exc)
                        self._model = TransformersEmbeddingModel(self.model_path, self.device)
                    logger.info("本地 embedding 模型加载完成")
        return self._model

    def encode_text(self, text: str) -> List[float]:
        embeddings = self.encode_texts([text])
        return embeddings[0] if embeddings else []

    def encode_texts(self, texts: List[str]) -> List[List[float]]:
        vectors = self._load_model().encode(texts, normalize_embeddings=True)
        embeddings = [_to_float_list(vector) for vector in vectors]
        if embeddings:
            self.embedding_dim = len(embeddings[0])
        return embeddings

    def get_info(self) -> dict:
        return {
            "model_name": self.model_name,
            "embedding_dim": self.embedding_dim,
            "api_base_url": "local",
            "local_model_path": self.model_path,
            "local_device": self.device,
            "service_type": "local",
        }
