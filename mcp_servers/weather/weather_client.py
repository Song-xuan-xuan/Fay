import os
from urllib.parse import urlsplit

import requests


API_KEY_ENV_NAME = "HEFENG_API"
API_HOST_ENV_NAME = "HEFENG_API_HOST"
HTTPS_SCHEME = "https"
GEO_LOOKUP_PATH = "/geo/v2/city/lookup"
CURRENT_WEATHER_PATH = "/v7/weather/now"
API_KEY_HEADER_NAME = "X-QW-Api-Key"
REQUEST_TIMEOUT_SECONDS = 10
SUCCESS_HTTP_STATUS_MIN = 200
SUCCESS_HTTP_STATUS_MAX = 299
SERVER_ERROR_STATUS_MIN = 500
AUTH_HTTP_STATUSES = frozenset((401, 403))
AUTH_BUSINESS_CODES = frozenset(("401", "403"))
QUOTA_BUSINESS_CODES = frozenset(("402",))
QUOTA_HTTP_STATUS = 402
RATE_LIMIT_STATUS = 429
RATE_LIMIT_BUSINESS_CODE = "429"
SUCCESS_BUSINESS_CODE = "200"

EMPTY_CITY_MESSAGE = "城市名称不能为空"
MISSING_API_KEY_MESSAGE = "未配置环境变量 HEFENG_API"
MISSING_API_HOST_MESSAGE = "未配置环境变量 HEFENG_API_HOST"
INVALID_API_HOST_MESSAGE = "HEFENG_API_HOST 仅允许纯主机名"
CITY_NOT_FOUND_MESSAGE = "未找到城市：{}"
AUTHENTICATION_FAILED_MESSAGE = "天气服务认证失败"
QUOTA_EXHAUSTED_MESSAGE = "天气服务配额已用尽"
RATE_LIMITED_MESSAGE = "天气服务请求过于频繁"
SERVICE_UNAVAILABLE_MESSAGE = "天气服务暂时不可用"
REQUEST_FAILED_MESSAGE = "天气服务请求失败"
BUSINESS_ERROR_MESSAGE = "天气服务返回错误"
REQUEST_TIMEOUT_MESSAGE = "天气服务请求超时"
INVALID_RESPONSE_MESSAGE = "天气服务响应格式错误"
INCOMPLETE_RESPONSE_MESSAGE = "天气服务响应数据不完整"


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


def _raise_for_http_status(status_code):
    if SUCCESS_HTTP_STATUS_MIN <= status_code <= SUCCESS_HTTP_STATUS_MAX:
        return
    if status_code in AUTH_HTTP_STATUSES:
        raise WeatherQueryError(AUTHENTICATION_FAILED_MESSAGE)
    if status_code == QUOTA_HTTP_STATUS:
        raise WeatherQueryError(QUOTA_EXHAUSTED_MESSAGE)
    if status_code == RATE_LIMIT_STATUS:
        raise WeatherQueryError(RATE_LIMITED_MESSAGE)
    if status_code >= SERVER_ERROR_STATUS_MIN:
        raise WeatherQueryError(SERVICE_UNAVAILABLE_MESSAGE)
    raise WeatherQueryError(REQUEST_FAILED_MESSAGE)


def _raise_for_business_code(payload):
    if not isinstance(payload, dict):
        raise WeatherQueryError(INVALID_RESPONSE_MESSAGE)
    code = str(payload.get("code", ""))
    if code == SUCCESS_BUSINESS_CODE:
        return
    if code in AUTH_BUSINESS_CODES:
        raise WeatherQueryError(AUTHENTICATION_FAILED_MESSAGE)
    if code in QUOTA_BUSINESS_CODES:
        raise WeatherQueryError(QUOTA_EXHAUSTED_MESSAGE)
    if code == RATE_LIMIT_BUSINESS_CODE:
        raise WeatherQueryError(RATE_LIMITED_MESSAGE)
    raise WeatherQueryError(BUSINESS_ERROR_MESSAGE)


def _request_json(session, url, api_key, params):
    request_error = None
    try:
        response = session.get(
            url,
            params=params,
            headers={API_KEY_HEADER_NAME: api_key},
            timeout=REQUEST_TIMEOUT_SECONDS,
            allow_redirects=False,
        )
    except requests.Timeout:
        request_error = REQUEST_TIMEOUT_MESSAGE
    except requests.RequestException:
        request_error = REQUEST_FAILED_MESSAGE
    if request_error:
        raise WeatherQueryError(request_error)
    _raise_for_http_status(response.status_code)
    invalid_json = False
    try:
        payload = response.json()
    except ValueError:
        invalid_json = True
    if invalid_json:
        raise WeatherQueryError(INVALID_RESPONSE_MESSAGE)
    _raise_for_business_code(payload)
    return payload


def _get_location(geo_data, requested_city):
    locations = geo_data.get("location")
    if not isinstance(locations, list):
        raise WeatherQueryError(INCOMPLETE_RESPONSE_MESSAGE)
    if not locations:
        raise WeatherQueryError(CITY_NOT_FOUND_MESSAGE.format(requested_city))
    location = locations[0]
    if not isinstance(location, dict):
        raise WeatherQueryError(INCOMPLETE_RESPONSE_MESSAGE)
    if not location.get("id") or not location.get("name"):
        raise WeatherQueryError(INCOMPLETE_RESPONSE_MESSAGE)
    return location


def _get_weather_now(weather_data):
    now = weather_data.get("now")
    if not isinstance(now, dict):
        raise WeatherQueryError(INCOMPLETE_RESPONSE_MESSAGE)
    if not now.get("text") or not now.get("temp"):
        raise WeatherQueryError(INCOMPLETE_RESPONSE_MESSAGE)
    return now


def _format_weather_summary(city_name, now):
    parts = [f"{city_name}：{now['text']}", f"温度 {now['temp']}°C"]
    optional_fields = (
        ("feelsLike", "体感 {}°C"),
        ("humidity", "湿度 {}%"),
        ("vis", "能见度 {} km"),
        ("obsTime", "观测时间 {}"),
    )
    for field_name, template in optional_fields[:2]:
        value = now.get(field_name)
        if value:
            parts.append(template.format(value))
    wind_dir = now.get("windDir", "")
    wind_scale = now.get("windScale", "")
    if wind_dir and wind_scale:
        parts.append(f"{wind_dir} {wind_scale}级")
    elif wind_dir:
        parts.append(wind_dir)
    elif wind_scale:
        parts.append(f"{wind_scale}级")
    for field_name, template in optional_fields[2:]:
        value = now.get(field_name)
        if value:
            parts.append(template.format(value))
    return "，".join(parts)


def query_current_weather(city_name, session=None):
    city = city_name.strip() if isinstance(city_name, str) else ""
    if not city:
        raise WeatherQueryError(EMPTY_CITY_MESSAGE)

    api_key = os.getenv(API_KEY_ENV_NAME, "").strip()
    if not api_key:
        raise WeatherQueryError(MISSING_API_KEY_MESSAGE)

    host = _normalize_host(os.getenv(API_HOST_ENV_NAME))
    http_session = session or requests
    base_url = f"{HTTPS_SCHEME}://{host}"
    geo_data = _request_json(
        http_session,
        f"{base_url}{GEO_LOOKUP_PATH}",
        api_key,
        {"location": city},
    )
    location = _get_location(geo_data, city)
    weather_data = _request_json(
        http_session,
        f"{base_url}{CURRENT_WEATHER_PATH}",
        api_key,
        {"location": location["id"]},
    )
    now = _get_weather_now(weather_data)
    return _format_weather_summary(location["name"], now)
