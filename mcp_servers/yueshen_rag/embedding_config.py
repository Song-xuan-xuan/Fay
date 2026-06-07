import os
from typing import Any, Dict, Optional


def allow_embedding_override() -> bool:
    return os.getenv("YUESHEN_ALLOW_EMBED_OVERRIDE", "0") == "1"


def embedding_tool_properties() -> Dict[str, Dict[str, str]]:
    if not allow_embedding_override():
        return {}
    return {
        "embedding_base_url": {"type": "string", "description": "Embedding API base url"},
        "embedding_api_key": {"type": "string", "description": "Embedding API key"},
        "embedding_model": {"type": "string", "description": "Embedding model name"},
    }


def resolve_embedding_kwargs(arguments: Dict[str, Any]) -> Dict[str, Optional[str]]:
    if not allow_embedding_override():
        return {
            "embedding_base_url": None,
            "embedding_api_key": None,
            "embedding_model": None,
        }
    return {
        "embedding_base_url": arguments.get("embedding_base_url"),
        "embedding_api_key": arguments.get("embedding_api_key"),
        "embedding_model": arguments.get("embedding_model"),
    }
