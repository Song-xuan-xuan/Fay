import json
import os
import time


DEFAULT_DB_PATH = os.path.join('memory', 'tourism_recommendation.db')


def now_seconds():
    return int(time.time())


def json_loads(value, fallback=None):
    try:
        return json.loads(value or '')
    except Exception:
        return [] if fallback is None else fallback


def json_dumps(value):
    return json.dumps(value if value is not None else {}, ensure_ascii=False)


def tags_from_value(value):
    if isinstance(value, str):
        value = value.split(',')
    return [str(item).strip() for item in (value or []) if str(item).strip()]


def bool_int(value):
    if isinstance(value, bool):
        return int(value)
    if value is None:
        return 0
    if isinstance(value, str):
        return int(value.strip().lower() in ('1', 'true', 'yes', 'on'))
    return int(bool(value))


def row_to_dict(row):
    if row is None:
        return None
    return dict(row)
