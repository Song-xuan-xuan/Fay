import os
from urllib.parse import urlsplit


API_KEY_ENV_NAME = "HEFENG_API"
API_HOST_ENV_NAME = "HEFENG_API_HOST"
HTTPS_SCHEME = "https"

EMPTY_CITY_MESSAGE = "city_name 不能为空"
MISSING_API_KEY_MESSAGE = "缺少 HEFENG_API 配置"
MISSING_API_HOST_MESSAGE = "缺少 HEFENG_API_HOST 配置"
INVALID_API_HOST_MESSAGE = "HEFENG_API_HOST 必须是纯主机名"
HTTP_NOT_IMPLEMENTED_MESSAGE = "天气 HTTP 请求将在后续任务实现"


class WeatherQueryError(ValueError):
    """天气查询输入或配置错误。"""


def _normalize_host(raw_host):
    host = (raw_host or "").strip().lower()
    if not host:
        raise WeatherQueryError(MISSING_API_HOST_MESSAGE)

    try:
        parsed = urlsplit(f"{HTTPS_SCHEME}://{host}")
        has_port = parsed.port is not None
    except ValueError as exc:
        raise WeatherQueryError(INVALID_API_HOST_MESSAGE) from exc

    labels = host.rstrip(".").split(".")
    labels_are_valid = all(
        label
        and label[0].isalnum()
        and label[-1].isalnum()
        and label.replace("-", "").isalnum()
        for label in labels
    )
    has_url_parts = bool(parsed.path or parsed.query or parsed.fragment)
    has_credentials = parsed.username is not None or parsed.password is not None
    if (
        parsed.scheme != HTTPS_SCHEME
        or parsed.netloc != host
        or parsed.hostname != host.rstrip(".")
        or has_port
        or has_url_parts
        or has_credentials
        or not labels_are_valid
    ):
        raise WeatherQueryError(INVALID_API_HOST_MESSAGE)

    return host


def query_current_weather(city_name):
    city = city_name.strip() if isinstance(city_name, str) else ""
    if not city:
        raise WeatherQueryError(EMPTY_CITY_MESSAGE)

    api_key = os.getenv(API_KEY_ENV_NAME, "").strip()
    if not api_key:
        raise WeatherQueryError(MISSING_API_KEY_MESSAGE)

    _normalize_host(os.getenv(API_HOST_ENV_NAME))
    raise NotImplementedError(HTTP_NOT_IMPLEMENTED_MESSAGE)
