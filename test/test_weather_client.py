import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from mcp_servers.weather.weather_client import WeatherQueryError, query_current_weather


API_KEY = "test-api-key"
API_HOST = "api.example.com"


class WeatherClientValidationTest(unittest.TestCase):
    def assert_query_error(self, city_name, environment, *, expected_message):
        with patch.dict(os.environ, environment, clear=True):
            with self.assertRaises(WeatherQueryError) as context:
                query_current_weather(city_name)

        actual_message = str(context.exception)
        self.assertEqual(expected_message, actual_message)
        self.assertNotIn(API_KEY, actual_message)

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

    def test_valid_configuration_reaches_http_stage(self):
        environment = {
            "HEFENG_API": API_KEY,
            "HEFENG_API_HOST": API_HOST,
        }

        with patch.dict(os.environ, environment, clear=True):
            with self.assertRaises(NotImplementedError) as context:
                query_current_weather("上海")

        actual_message = str(context.exception)
        self.assertEqual("天气 HTTP 请求将在后续任务实现", actual_message)
        self.assertNotIn(API_KEY, actual_message)


if __name__ == "__main__":
    unittest.main()
