import json
import os
import re
from datetime import datetime
from urllib.parse import quote, urlencode, urlsplit, urlunsplit

from core import digital_human_service
from utils import config_util


DEFAULT_SAMPLES_ROOT = os.path.join("library", "live2d", "Samples")
DEFAULT_RENDER_URL = "http://127.0.0.1:5174"
IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".gif")
COVER_KEYWORDS = ("cover", "preview", "thumbnail", "thumb", "avatar", "icon", "stand", "poster", "立绘", "封面")
TEXTURE_ATLAS_PATTERN = re.compile(r"(^|[\\/])[^\\/]+\.\d+[\\/].*texture[_-]?\d*\.(?:png|jpg|jpeg|webp)$", re.I)
SAFE_MODEL_NAME = re.compile(r"^[A-Za-z0-9_-]+$")
MOC3_MAGIC = b"MOC3"
MOC3_VERSION_OFFSET = 4
MOC3_HEADER_SIZE = 8
MAX_SUPPORTED_MOC3_VERSION = 5
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIVE2D_CONFIG_KEY = "live2d"
SAMPLES_ROOT_CONFIG_KEY = "samples_root"
RENDER_BASE_URL_CONFIG_KEY = "render_base_url"
IGNORED_MODELS_CONFIG_KEY = "ignored_models"
RESOURCE_SYNC_FIELDS = ("type", "render_url", "model_name")


def _now_text():
    return datetime.now().replace(microsecond=0).isoformat()


def samples_root():
    root = os.environ.get("FAY_LIVE2D_SAMPLES_ROOT") or _configured_samples_root()
    return _project_relative_path(root)


def _configured_samples_root():
    return _live2d_config_value(SAMPLES_ROOT_CONFIG_KEY, DEFAULT_SAMPLES_ROOT)


def configured_render_base_url():
    return _live2d_config_value(RENDER_BASE_URL_CONFIG_KEY, DEFAULT_RENDER_URL)


def ignored_model_names():
    config = config_util.config if isinstance(config_util.config, dict) else {}
    live2d_config = config.get(LIVE2D_CONFIG_KEY)
    if not isinstance(live2d_config, dict):
        return set()
    ignored = live2d_config.get(IGNORED_MODELS_CONFIG_KEY) or []
    if not isinstance(ignored, list):
        return set()
    return {str(item).strip().lower() for item in ignored if str(item).strip()}


def _live2d_config_value(key, default):
    config = config_util.config if isinstance(config_util.config, dict) else {}
    live2d_config = config.get(LIVE2D_CONFIG_KEY)
    if isinstance(live2d_config, dict):
        value = live2d_config.get(key)
        if value:
            return value
    return default


def _project_relative_path(path):
    if os.path.isabs(path):
        return os.path.abspath(path)
    return os.path.abspath(os.path.join(PROJECT_ROOT, path))


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


def _cover_candidate_rank(relative_path):
    normalized = relative_path.replace("\\", "/")
    if TEXTURE_ATLAS_PATTERN.search(normalized):
        return None
    filename = os.path.basename(normalized).lower()
    stem = os.path.splitext(filename)[0]
    for index, keyword in enumerate(COVER_KEYWORDS):
        if keyword in stem:
            depth = normalized.count("/")
            return (index, depth, normalized.lower())
    return None


def _cover_url(model_dir, model_name):
    candidates = []
    for root, _, files in os.walk(model_dir):
        for filename in sorted(files):
            if filename.lower().endswith(IMAGE_EXTENSIONS):
                full_path = os.path.join(root, filename)
                relative_path = os.path.relpath(full_path, model_dir)
                rank = _cover_candidate_rank(relative_path)
                if rank is not None:
                    candidates.append((rank, relative_path))
    if candidates:
        _, relative_path = sorted(candidates, key=lambda item: item[0])[0]
        return _resource_url(model_name, relative_path)
    return digital_human_service.DEFAULT_COVER_URL


def _model_json_path(model_dir, model_name):
    return os.path.join(model_dir, f"{model_name}.model3.json")


def _model_json_exists(model_dir, model_name):
    return os.path.isfile(_model_json_path(model_dir, model_name))


def _model_moc_path(model_dir, model_name):
    moc_file = f"{model_name}.moc3"
    try:
        with open(_model_json_path(model_dir, model_name), "r", encoding="utf-8") as file:
            model_json = json.load(file)
        references = model_json.get("FileReferences") if isinstance(model_json, dict) else {}
        if isinstance(references, dict) and references.get("Moc"):
            moc_file = references["Moc"]
    except (OSError, ValueError, TypeError):
        pass

    base_dir = os.path.abspath(model_dir)
    moc_path = os.path.abspath(os.path.join(base_dir, moc_file))
    if os.path.commonpath([base_dir, moc_path]) != base_dir:
        return None
    return moc_path


def _moc3_version(moc_path):
    if not moc_path or not os.path.isfile(moc_path):
        return None
    with open(moc_path, "rb") as file:
        header = file.read(MOC3_HEADER_SIZE)
    if len(header) < MOC3_HEADER_SIZE or not header.startswith(MOC3_MAGIC):
        return None
    return header[MOC3_VERSION_OFFSET]


def _is_supported_moc3_model(model_dir, model_name):
    try:
        version = _moc3_version(_model_moc_path(model_dir, model_name))
    except OSError:
        return True
    return version is None or version <= MAX_SUPPORTED_MOC3_VERSION


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


def discover_live2d_resource_models(root=None, render_base_url=None):
    root_dir = resources_root(root)
    if not os.path.isdir(root_dir):
        return []
    effective_render_base_url = render_base_url or configured_render_base_url()
    ignored_models = ignored_model_names()
    models = []
    for entry in sorted(os.scandir(root_dir), key=lambda item: item.name.lower()):
        if not entry.is_dir() or not SAFE_MODEL_NAME.match(entry.name):
            continue
        if entry.name.lower() in ignored_models:
            continue
        if _model_json_exists(entry.path, entry.name) and _is_supported_moc3_model(entry.path, entry.name):
            models.append(_to_digital_human(entry.name, entry.path, effective_render_base_url))
    return models


def import_live2d_resource_models(root=None, render_base_url=None):
    cfg = digital_human_service.ensure_digital_humans_config()
    existing_indices = {item.get("id"): index for index, item in enumerate(cfg["digital_humans"]["items"])}
    discovered = discover_live2d_resource_models(root, render_base_url)
    imported = []
    updated = []
    skipped = []
    for human in discovered:
        existing_index = existing_indices.get(human["id"])
        if existing_index is not None:
            existing = cfg["digital_humans"]["items"][existing_index]
            if _sync_resource_fields(existing, human):
                updated.append(existing.copy())
            else:
                skipped.append(human)
            continue
        cfg["digital_humans"]["items"].append(human)
        existing_indices[human["id"]] = len(cfg["digital_humans"]["items"]) - 1
        imported.append(human)
    if imported or updated:
        digital_human_service.persist_config(cfg, sections=("digital_humans",))
    return {"imported": imported, "updated": updated, "skipped": skipped, "items": discovered}


def _sync_resource_fields(existing, discovered):
    changed = False
    for field in RESOURCE_SYNC_FIELDS:
        if field in discovered and existing.get(field) != discovered[field]:
            existing[field] = discovered[field]
            changed = True
    if _should_sync_cover_url(existing.get("cover_url"), discovered.get("cover_url")):
        existing["cover_url"] = discovered["cover_url"]
        changed = True
    if changed:
        existing["updated_at"] = _now_text()
    return changed


def _should_sync_cover_url(existing_cover, discovered_cover):
    if not discovered_cover or existing_cover == discovered_cover:
        return False
    return _is_default_cover_url(existing_cover)


def _is_default_cover_url(cover_url):
    return (
        not cover_url
        or cover_url == digital_human_service.DEFAULT_COVER_URL
        or cover_url in digital_human_service.LEGACY_DEFAULT_COVER_URLS
    )


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
