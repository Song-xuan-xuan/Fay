# -*- coding: utf-8 -*-
"""Helpers for preparing image references for OpenAI-compatible vision APIs."""

from __future__ import annotations

import base64
import mimetypes
import os
from typing import Optional
from urllib.parse import unquote, urlparse


INTERNAL_IMAGE_PREFIX = "/api/get-image/"
DEFAULT_IMAGE_BASE_DIR = os.path.join("cache_data", "images")


def _safe_join(base_dir: str, *parts: str) -> Optional[str]:
    base_path = os.path.abspath(base_dir)
    candidate = os.path.abspath(os.path.join(base_path, *parts))
    try:
        if os.path.commonpath([base_path, candidate]) != base_path:
            return None
    except ValueError:
        return None
    return candidate


def _file_to_data_url(path: str) -> Optional[str]:
    if not os.path.isfile(path):
        return None
    mime_type = mimetypes.guess_type(path)[0] or "image/jpeg"
    if not mime_type.startswith("image/"):
        return None
    with open(path, "rb") as file:
        encoded = base64.b64encode(file.read()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _internal_route_to_path(image_ref: str, base_dir: str) -> Optional[str]:
    parsed = urlparse(image_ref)
    route_path = parsed.path if parsed.scheme else image_ref
    if not route_path.startswith(INTERNAL_IMAGE_PREFIX):
        return None
    relative = route_path[len(INTERNAL_IMAGE_PREFIX):]
    parts = [unquote(part) for part in relative.split("/") if part]
    if len(parts) != 3 or any(part in (".", "..") for part in parts):
        return None
    return _safe_join(base_dir, *parts)


def image_ref_to_llm_url(image_ref: str, base_dir: str = DEFAULT_IMAGE_BASE_DIR) -> Optional[str]:
    """Return a URL that a remote vision API can read, or None if unusable."""
    if not image_ref or not isinstance(image_ref, str):
        return None
    ref = image_ref.strip()
    if ref.startswith("data:image/"):
        return ref

    internal_path = _internal_route_to_path(ref, base_dir)
    if internal_path:
        return _file_to_data_url(internal_path)

    parsed = urlparse(ref)
    if parsed.scheme in ("http", "https"):
        return ref

    direct_path = os.path.abspath(ref)
    return _file_to_data_url(direct_path)
