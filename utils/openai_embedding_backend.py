import logging
import time
from typing import List

import requests

logger = logging.getLogger(__name__)


def normalize_embeddings_url(api_base_url: str) -> str:
    base_url = (api_base_url or "").strip().rstrip("/")
    if base_url.endswith("/embeddings"):
        return base_url
    if base_url.endswith("/chat/completions"):
        return f"{base_url[:-len('/chat/completions')]}/embeddings"
    return f"{base_url}/embeddings"


class OpenAIEmbeddingBackend:
    def __init__(
        self,
        api_base_url: str,
        api_key: str,
        model_name: str,
        timeout: int = 60,
        max_retries: int = 2,
    ):
        self.api_base_url = api_base_url.rstrip("/")
        self.embeddings_url = normalize_embeddings_url(api_base_url)
        self.api_key = api_key
        self.model_name = model_name
        self.timeout = timeout
        self.max_retries = max_retries
        self.embedding_dim = None

    def encode_text(self, text: str) -> List[float]:
        for attempt in range(self.max_retries + 1):
            try:
                embedding = self._post_embeddings(text, self.timeout)[0]
                self._update_dim(embedding)
                return embedding
            except requests.exceptions.HTTPError:
                raise
            except Exception as exc:
                if attempt >= self.max_retries:
                    raise
                wait_time = 2 ** attempt
                logger.warning("embedding 请求失败，%s 秒后重试: %s", wait_time, exc)
                time.sleep(wait_time)
        return []

    def encode_texts(self, texts: List[str]) -> List[List[float]]:
        embeddings = self._post_embeddings(texts, self.timeout * 2)
        for embedding in embeddings:
            self._update_dim(embedding)
        return embeddings

    def _post_embeddings(self, input_value, timeout: int) -> List[List[float]]:
        payload = {"model": self.model_name, "input": input_value}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        response = requests.post(self.embeddings_url, json=payload, headers=headers, timeout=timeout)
        response.raise_for_status()
        result = response.json()
        return [item["embedding"] for item in result["data"]]

    def _update_dim(self, embedding: List[float]) -> None:
        current_dim = len(embedding)
        if self.embedding_dim is None:
            self.embedding_dim = current_dim
        elif current_dim != self.embedding_dim:
            logger.warning(
                "Embedding 维度不一致: expected=%s actual=%s",
                self.embedding_dim,
                current_dim,
            )
            self.embedding_dim = current_dim

    def get_info(self) -> dict:
        return {
            "model_name": self.model_name,
            "embedding_dim": self.embedding_dim,
            "api_base_url": self.api_base_url,
            "local_model_path": None,
            "local_device": None,
            "service_type": "api",
        }
