import os
import re
from datetime import datetime
from urllib.parse import quote, urlencode, urlsplit, urlunsplit

from core import digital_human_service


DEFAULT_SAMPLES_ROOT = os.path.join("library", "live2d", "Samples")
DEFAULT_RENDER_URL = "http://127.0.0.1:5174"
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".gif")
SAFE_MODEL_NAME = re.compile(r"^[A-Za-z0-9_-]+$")


def _now_text():
    return datetime.now().replace(microsecond=0).isoformat()


def samples_root():
    root = os.environ.get("FAY_LIVE2D_SAMPLES_ROOT") or DEFAULT_SAMPLES_ROOT
    return os.path.abspath(root)


def resources_root(root=None):
    return os.path.abspath(os.path.join(root or samples_root(), "Resources"))


def _slug(value):
    text = re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_").lower()
    return text or "model"


def _model_id(model_name):
    return f"live2d_{_slug(model_name)}"


def _render_url(base_url, model_name):
    parts = urlsplit(base_url or DEFAULT_RENDER_URL)
    query = parts.query
    model_query = urlencode({"model": model_name})
    next_query = f"{query}&{model_query}" if query else model_query
    return urlunsplit((parts.scheme, parts.netloc, parts.path, next_query, parts.fragment))


def _resource_url(model_name, relative_path):
    path = "/".join(quote(part) for part in relative_path.replace("\\", "/").split("/"))
    return f"/digital-humans/live2d-resources/{quote(model_name)}/{path}"


def _cover_url(model_dir, model_name):
    for root, _, files in os.walk(model_dir):
        for filename in sorted(files):
            if filename.lower().endswith(IMAGE_EXTENSIONS):
                full_path = os.path.join(root, filename)
                relative_path = os.path.relpath(full_path, model_dir)
                return _resource_url(model_name, relative_path)
    return digital_human_service.DEFAULT_COVER_URL


def _model_json_exists(model_dir, model_name):
    return os.path.isfile(os.path.join(model_dir, f"{model_name}.model3.json"))


def _to_digital_human(model_name, model_dir, render_base_url):
    now = _now_text()
    return {
        "id": _model_id(model_name),
        "name": model_name,
        "type": "live2d",
        "model_name": model_name,
        "cover_url": _cover_url(model_dir, model_name),
        "render_url": _render_url(render_base_url, model_name),
        "voice": "",
        "tags": ["Live2D", model_name],
        "persona": {
            "gender": "",
            "age": "",
            "birth": "",
            "zodiac": "",
            "constellation": "",
            "position": "数字人",
            "goal": "互动展示",
            "job": "",
            "contact": "",
            "additional": f"Live2D 模型：{model_name}",
        },
        "enabled": True,
        "created_at": now,
        "updated_at": now,
    }


def discover_live2d_resource_models(root=None, render_base_url=DEFAULT_RENDER_URL):
    root_dir = resources_root(root)
    if not os.path.isdir(root_dir):
        return []
    models = []
    for entry in sorted(os.scandir(root_dir), key=lambda item: item.name.lower()):
        if not entry.is_dir() or not SAFE_MODEL_NAME.match(entry.name):
            continue
        if _model_json_exists(entry.path, entry.name):
            models.append(_to_digital_human(entry.name, entry.path, render_base_url))
    return models


def import_live2d_resource_models(root=None, render_base_url=DEFAULT_RENDER_URL):
    cfg = digital_human_service.ensure_digital_humans_config()
    existing_ids = {item.get("id") for item in cfg["digital_humans"]["items"]}
    discovered = discover_live2d_resource_models(root, render_base_url)
    imported = []
    skipped = []
    for human in discovered:
        if human["id"] in existing_ids:
            skipped.append(human)
            continue
        cfg["digital_humans"]["items"].append(human)
        existing_ids.add(human["id"])
        imported.append(human)
    if imported:
        digital_human_service.persist_config(cfg, sections=("digital_humans",))
    return {"imported": imported, "skipped": skipped, "items": discovered}


def resolve_resource_path(model_name, relative_path, root=None):
    if not SAFE_MODEL_NAME.match(model_name or ""):
        raise ValueError("模型名称不合法")
    base_dir = os.path.abspath(os.path.join(resources_root(root), model_name))
    target_path = os.path.abspath(os.path.join(base_dir, relative_path))
    if os.path.commonpath([base_dir, target_path]) != base_dir:
        raise ValueError("资源路径不合法")
    if not os.path.isfile(target_path):
        raise ValueError("资源不存在")
    return base_dir, os.path.relpath(target_path, base_dir).replace(os.sep, "/")
