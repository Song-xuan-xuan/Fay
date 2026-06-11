import copy
import os
import uuid
from datetime import datetime

from utils import config_util


VALID_TYPES = {"live2d", "iframe", "image"}
DEFAULT_HUMAN_ID = "fay_default"
DEFAULT_RENDER_URL = "http://127.0.0.1:5174"
DEFAULT_COVER_URL = "/static/images/Normal.gif"
PERSONA_KEYS = (
    "gender",
    "age",
    "birth",
    "zodiac",
    "constellation",
    "position",
    "goal",
    "job",
    "contact",
    "additional",
)
ATTRIBUTE_KEYS = ("name", "voice", *PERSONA_KEYS)


def _now_text():
    return datetime.now().replace(microsecond=0).isoformat()


def _as_text(value):
    if value is None:
        return ""
    return str(value).strip()


def _runtime_config(config=None):
    if config is not None:
        return config
    if config_util.config is None:
        config_util.load_config()
    return config_util.config


def _attribute_to_persona(attribute):
    return {key: _as_text(attribute.get(key)) for key in PERSONA_KEYS}


def _default_human_from_attribute(attribute):
    name = _as_text(attribute.get("name")) or "Fay"
    now = _now_text()
    return {
        "id": DEFAULT_HUMAN_ID,
        "name": name,
        "type": "live2d",
        "cover_url": DEFAULT_COVER_URL,
        "render_url": DEFAULT_RENDER_URL,
        "voice": _as_text(attribute.get("voice")),
        "tags": [],
        "persona": _attribute_to_persona(attribute),
        "enabled": True,
        "created_at": now,
        "updated_at": now,
    }


def _normalize_tags(value):
    if isinstance(value, str):
        values = value.split(",")
    elif isinstance(value, list):
        values = value
    else:
        values = []
    return [text for text in (_as_text(item) for item in values) if text]


def _normalize_persona(value):
    source = value if isinstance(value, dict) else {}
    return {key: _as_text(source.get(key)) for key in PERSONA_KEYS}


def _make_human_id(payload):
    raw_id = _as_text(payload.get("id"))
    if raw_id:
        return raw_id
    return f"dh_{uuid.uuid4().hex[:12]}"


def _normalize_human(payload, existing=None):
    source = payload if isinstance(payload, dict) else {}
    current = existing if isinstance(existing, dict) else {}
    human_type = _as_text(source.get("type", current.get("type") or "live2d"))
    if human_type not in VALID_TYPES:
        raise ValueError("不支持的数字人类型")
    now = _now_text()
    human = {
        "id": _as_text(current.get("id")) or _make_human_id(source),
        "name": _as_text(source.get("name", current.get("name"))) or "未命名数字人",
        "type": human_type,
        "cover_url": _as_text(source.get("cover_url", current.get("cover_url"))),
        "render_url": _as_text(source.get("render_url", current.get("render_url"))),
        "voice": _as_text(source.get("voice", current.get("voice"))),
        "tags": _normalize_tags(source.get("tags", current.get("tags", []))),
        "persona": _normalize_persona(source.get("persona", current.get("persona", {}))),
        "enabled": bool(source.get("enabled", current.get("enabled", True))),
        "created_at": _as_text(current.get("created_at")) or now,
        "updated_at": now,
    }
    if not human["cover_url"]:
        human["cover_url"] = DEFAULT_COVER_URL
    if human["type"] in ("live2d", "iframe") and not human["render_url"]:
        human["render_url"] = DEFAULT_RENDER_URL
    return human


def ensure_digital_humans_config(config=None):
    cfg = _runtime_config(config)
    attribute = cfg.setdefault("attribute", {})
    digital_humans = cfg.get("digital_humans")
    if not isinstance(digital_humans, dict):
        cfg["digital_humans"] = {
            "active_id": DEFAULT_HUMAN_ID,
            "items": [_default_human_from_attribute(attribute)],
        }
        return cfg

    items = digital_humans.get("items")
    if not isinstance(items, list) or not items:
        digital_humans["items"] = [_default_human_from_attribute(attribute)]
        digital_humans["active_id"] = DEFAULT_HUMAN_ID
        return cfg

    normalized = [_normalize_human(item) for item in items if isinstance(item, dict)]
    digital_humans["items"] = normalized or [_default_human_from_attribute(attribute)]
    ids = {item["id"] for item in digital_humans["items"]}
    if _as_text(digital_humans.get("active_id")) not in ids:
        digital_humans["active_id"] = digital_humans["items"][0]["id"]
    return cfg


def _all_search_text(human):
    persona = human.get("persona") or {}
    parts = [
        human.get("name"),
        human.get("type"),
        human.get("voice"),
        " ".join(human.get("tags") or []),
        " ".join(_as_text(persona.get(key)) for key in PERSONA_KEYS),
    ]
    return " ".join(_as_text(part).lower() for part in parts)


def _keyword_matches(human, keyword):
    tokens = [_as_text(part).lower() for part in _as_text(keyword).split() if _as_text(part)]
    if not tokens:
        return True
    searchable = _all_search_text(human)
    return all(token in searchable for token in tokens)


def list_digital_humans(keyword="", human_type="", config=None):
    cfg = ensure_digital_humans_config(_runtime_config(config))
    target_type = _as_text(human_type)
    items = []
    for human in cfg["digital_humans"]["items"]:
        if target_type and human.get("type") != target_type:
            continue
        if _keyword_matches(human, keyword):
            items.append(copy.deepcopy(human))
    return items


def _find_human_index(human_id, config=None):
    cfg = ensure_digital_humans_config(_runtime_config(config))
    target_id = _as_text(human_id)
    for index, human in enumerate(cfg["digital_humans"]["items"]):
        if human.get("id") == target_id:
            return cfg, index
    raise ValueError("数字人不存在")


def get_active_digital_human(config=None):
    cfg = ensure_digital_humans_config(_runtime_config(config))
    active_id = _as_text(cfg["digital_humans"].get("active_id"))
    for human in cfg["digital_humans"]["items"]:
        if human.get("id") == active_id:
            return copy.deepcopy(human)
    return copy.deepcopy(cfg["digital_humans"]["items"][0])


def persist_config(config, sections=None):
    if sections and hasattr(config_util, "save_config_sections"):
        config_util.save_config_sections(config, sections)
    else:
        config_util.save_config(config)
    config_util.load_config(force_reload=True)


def create_digital_human(payload, persist=True):
    cfg = ensure_digital_humans_config()
    human = _normalize_human(payload or {})
    existing_ids = {item["id"] for item in cfg["digital_humans"]["items"]}
    if human["id"] in existing_ids:
        raise ValueError("数字人 ID 已存在")
    cfg["digital_humans"]["items"].append(human)
    if persist:
        persist_config(cfg, sections=("digital_humans",))
    return copy.deepcopy(human)


def update_digital_human(human_id, payload, persist=True):
    cfg, index = _find_human_index(human_id)
    current = cfg["digital_humans"]["items"][index]
    updated = _normalize_human(payload or {}, existing=current)
    cfg["digital_humans"]["items"][index] = updated
    if cfg["digital_humans"].get("active_id") == updated["id"]:
        _apply_human_to_attribute(cfg, updated)
    if persist:
        sections = ("digital_humans", "attribute") if cfg["digital_humans"].get("active_id") == updated["id"] else ("digital_humans",)
        persist_config(cfg, sections=sections)
    return copy.deepcopy(updated)


def delete_digital_human(human_id, persist=True):
    cfg, index = _find_human_index(human_id)
    if cfg["digital_humans"].get("active_id") == _as_text(human_id):
        raise ValueError("不能删除当前启用的数字人")
    deleted = cfg["digital_humans"]["items"].pop(index)
    if persist:
        persist_config(cfg, sections=("digital_humans",))
    return copy.deepcopy(deleted)


def _apply_human_to_attribute(config, human):
    attribute = config.setdefault("attribute", {})
    attribute["name"] = human.get("name") or attribute.get("name", "")
    attribute["voice"] = human.get("voice") or attribute.get("voice", "")
    persona = human.get("persona") or {}
    for key in PERSONA_KEYS:
        attribute[key] = _as_text(persona.get(key))


def activate_digital_human(human_id, persist=True):
    cfg, index = _find_human_index(human_id)
    human = cfg["digital_humans"]["items"][index]
    if not human.get("enabled", True):
        raise ValueError("数字人已禁用")
    cfg["digital_humans"]["active_id"] = human["id"]
    _apply_human_to_attribute(cfg, human)
    if persist:
        persist_config(cfg, sections=("digital_humans", "attribute"))
    return copy.deepcopy(human)


def sync_active_human_from_attribute(config=None, persist=False):
    cfg = ensure_digital_humans_config(_runtime_config(config))
    active_id = cfg["digital_humans"].get("active_id")
    _, index = _find_human_index(active_id, cfg)
    attribute = cfg.get("attribute") or {}
    human = cfg["digital_humans"]["items"][index]
    human["name"] = _as_text(attribute.get("name")) or human.get("name", "")
    human["voice"] = _as_text(attribute.get("voice"))
    human["persona"] = _attribute_to_persona(attribute)
    human["updated_at"] = _now_text()
    if persist:
        persist_config(cfg, sections=("digital_humans",))
    return copy.deepcopy(human)


def cover_dir(project_root=None):
    root = project_root or os.getcwd()
    return os.path.abspath(os.path.join(root, "cache_data", "digital_humans", "covers"))
