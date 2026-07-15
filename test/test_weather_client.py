import os
import sys
import unittest
from json import JSONDecodeError
from pathlib import Path
from unittest.mock import patch

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from mcp_servers.weather.weather_client import WeatherQueryError, query_current_weather


API_KEY = "test-api-key"
API_HOST = "api.example.com"
REQUEST_TIMEOUT_SECONDS = 10
API_KEY_HEADER = "X-QW-Api-Key"
GEO_URL = f"https://{API_HOST}/geo/v2/city/lookup"
WEATHER_URL = f"https://{API_HOST}/v7/weather/now"
RESPONSE_HEADER_SECRET = "response-header-secret"


class FakeResponse:
    def __init__(self, payload=None, status_code=200, json_error=None):
        self.payload = payload
        self.status_code = status_code
        self.json_error = json_error
        self.headers = {"X-Debug-Secret": RESPONSE_HEADER_SECRET}

    def json(self):
        if self.json_error:
            raise self.json_error
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


def responses_for_stage(stage, terminal_response):
    if stage == "geo":
        return [terminal_response]
    return [FakeResponse(qweather_geo_payload()), terminal_response]


def qweather_geo_payload():
    location = {
        "name": "上海",
        "id": "101020100",
        "lat": "31.23170",
        "lon": "121.47264",
        "adm2": "上海",
        "adm1": "上海市",
        "country": "中国",
        "tz": "Asia/Shanghai",
        "utcOffset": "+08:00",
        "isDst": "0",
        "type": "city",
        "rank": "11",
        "fxLink": "https://www.qweather.com/weather/shanghai-101020100.html",
    }
    alternate = {**location, "name": "上海县", "id": "second-location-id"}
    return {
        "code": "200",
        "location": [location, alternate],
        "refer": {"sources": ["QWeather"], "license": ["QWeather Developers License"]},
    }


def qweather_now_payload():
    return {
        "code": "200",
        "updateTime": "2026-07-15T10:04+08:00",
        "fxLink": "https://www.qweather.com/weather/shanghai-101020100.html",
        "now": {
            "obsTime": "2026-07-15T10:00+08:00",
            "temp": "26",
            "feelsLike": "28",
            "icon": "101",
            "text": "多云",
            "wind360": "135",
            "windDir": "东南风",
            "windScale": "3",
            "windSpeed": "12",
            "humidity": "65",
            "precip": "0.0",
            "pressure": "1005",
            "vis": "10",
            "cloud": "70",
            "dew": "19",
        },
        "refer": {"sources": ["QWeather"], "license": ["QWeather Developers License"]},
    }


class WeatherClientValidationTest(unittest.TestCase):
    def assert_safe(self, value):
        text = str(value)
        for secret in (
            API_KEY,
            API_KEY_HEADER,
            GEO_URL,
            WEATHER_URL,
            RESPONSE_HEADER_SECRET,
        ):
            self.assertNotIn(secret, text)
        if isinstance(value, BaseException):
            for linked_error in (value.__cause__, value.__context__):
                if linked_error:
                    self.assert_safe(str(linked_error))

    def query_with_session(self, session, city_name="上海"):
        environment = {"HEFENG_API": API_KEY, "HEFENG_API_HOST": API_HOST}
        with patch.dict(os.environ, environment, clear=True):
            return query_current_weather(city_name, session=session)

    def assert_weather_error(self, responses, expected_message):
        with self.assertRaises(WeatherQueryError) as context:
            self.query_with_session(FakeSession(responses))
        self.assertEqual(expected_message, str(context.exception))
        self.assert_safe(context.exception)

    def assert_query_error(self, city_name, environment, *, expected_message):
        with patch.dict(os.environ, environment, clear=True):
            with self.assertRaises(WeatherQueryError) as context:
                query_current_weather(city_name)

        actual_message = str(context.exception)
        self.assertEqual(expected_message, actual_message)
        self.assert_safe(actual_message)

    def test_queries_geo_then_weather_and_returns_summary(self):
        session = FakeSession(
            [FakeResponse(qweather_geo_payload()), FakeResponse(qweather_now_payload())]
        )
        environment = {"HEFENG_API": API_KEY, "HEFENG_API_HOST": API_HOST}

        with patch.dict(os.environ, environment, clear=True):
            result = query_current_weather(" 上海 ", session=session)

        self.assertEqual(
            "上海：多云，温度 26°C，体感 28°C，湿度 65%，东南风 3级，"
            "能见度 10 km，观测时间 2026-07-15T10:00+08:00",
            result,
        )
        self.assert_safe(result)
        self.assertEqual(2, len(session.calls))
        geo_url, geo_request = session.calls[0]
        weather_url, weather_request = session.calls[1]
        self.assertEqual(GEO_URL, geo_url)
        self.assertEqual({"location": "上海"}, geo_request["params"])
        self.assertEqual(WEATHER_URL, weather_url)
        self.assertEqual({"location": "101020100"}, weather_request["params"])
        for request in (geo_request, weather_request):
            self.assertEqual({"X-QW-Api-Key": API_KEY}, request["headers"])
            self.assertEqual(REQUEST_TIMEOUT_SECONDS, request["timeout"])
            self.assertFalse(request["allow_redirects"])

    def test_rejects_city_not_found(self):
        payload = {"code": "200", "location": [], "refer": {}}
        self.assert_weather_error([FakeResponse(payload)], "未找到城市：上海")

    def test_maps_http_status_errors(self):
        cases = (
            (401, "天气服务认证失败"),
            (403, "天气服务认证失败"),
            (429, "天气服务请求过于频繁"),
            (500, "天气服务暂时不可用"),
            (503, "天气服务暂时不可用"),
        )
        for status_code, expected_message in cases:
            with self.subTest(status_code=status_code):
                self.assert_weather_error(
                    [FakeResponse(status_code=status_code)], expected_message
                )

    def test_maps_business_code_errors_at_both_endpoints(self):
        cases = (
            ("401", "天气服务认证失败"),
            ("403", "天气服务认证失败"),
            ("402", "天气服务配额已用尽"),
            ("429", "天气服务请求过于频繁"),
            ("400", "天气服务返回错误"),
        )
        for stage in ("geo", "weather"):
            for code, expected_message in cases:
                with self.subTest(stage=stage, code=code):
                    response = FakeResponse({"code": code, "refer": {}})
                    self.assert_weather_error(
                        responses_for_stage(stage, response), expected_message
                    )

    def test_maps_transport_and_json_errors_at_both_endpoints(self):
        request_details = f"{API_KEY_HEADER}: {API_KEY}; {WEATHER_URL}"
        cases = (
            (requests.Timeout(request_details), "天气服务请求超时"),
            (requests.RequestException(request_details), "天气服务请求失败"),
            (
                FakeResponse(json_error=JSONDecodeError("bad", request_details, 0)),
                "天气服务响应格式错误",
            ),
        )
        for stage in ("geo", "weather"):
            for terminal, expected_message in cases:
                with self.subTest(stage=stage, expected_message=expected_message):
                    self.assert_weather_error(
                        responses_for_stage(stage, terminal), expected_message
                    )

    def test_rejects_incomplete_success_payloads(self):
        cases = (
            ([FakeResponse({"code": "200", "refer": {}})], "天气服务响应数据不完整"),
            (
                responses_for_stage("weather", FakeResponse({"code": "200"})),
                "天气服务响应数据不完整",
            ),
            (
                responses_for_stage(
                    "weather", FakeResponse({"code": "200", "now": {"temp": "26"}})
                ),
                "天气服务响应数据不完整",
            ),
            (
                responses_for_stage(
                    "weather", FakeResponse({"code": "200", "now": {"text": "多云"}})
                ),
                "天气服务响应数据不完整",
            ),
        )
        for responses, expected_message in cases:
            with self.subTest(responses=responses):
                self.assert_weather_error(responses, expected_message)

    def test_rejects_empty_city_name(self):
        environment = {
            "HEFENG_API": API_KEY,
            "HEFENG_API_HOST": API_HOST,
        }

        for city_name in ("", "   "):
            with self.subTest(city_name=city_name):
                self.assert_query_error(
                    city_name,
                    environment,
                    expected_message="城市名称不能为空",
                )

    def test_rejects_missing_api_key(self):
        environment = {"HEFENG_API_HOST": API_HOST}

        self.assert_query_error(
            "上海",
            environment,
            expected_message="未配置环境变量 HEFENG_API",
        )

    def test_rejects_missing_api_host(self):
        environment = {"HEFENG_API": API_KEY}

        self.assert_query_error(
            "上海",
            environment,
            expected_message="未配置环境变量 HEFENG_API_HOST",
        )

    def test_rejects_non_host_api_host(self):
        invalid_hosts = (
            "https://api.example.com",
            "api.example.com/v7/weather/now",
            "api.example.com?lang=zh",
            "api.example.com#weather",
        )

        for api_host in invalid_hosts:
            with self.subTest(api_host=api_host):
                environment = {
                    "HEFENG_API": API_KEY,
                    "HEFENG_API_HOST": api_host,
                }
                self.assert_query_error(
                    "上海",
                    environment,
                    expected_message="HEFENG_API_HOST 仅允许纯主机名",
                )

if __name__ == "__main__":
    unittest.main()
