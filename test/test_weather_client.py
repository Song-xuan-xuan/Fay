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
    def assert_query_rejected_without_http(self, city_name, environment):
        with (
            patch.dict(os.environ, environment, clear=True),
            patch("requests.get") as http_get,
            self.assertRaises(WeatherQueryError),
        ):
            query_current_weather(city_name)

        http_get.assert_not_called()

    def test_rejects_empty_city_name_without_http_request(self):
        environment = {
            "HEFENG_API": API_KEY,
            "HEFENG_API_HOST": API_HOST,
        }

        for city_name in ("", "   "):
            with self.subTest(city_name=city_name):
                self.assert_query_rejected_without_http(city_name, environment)

    def test_rejects_missing_api_key_without_http_request(self):
        environment = {"HEFENG_API_HOST": API_HOST}

        self.assert_query_rejected_without_http("上海", environment)

    def test_rejects_missing_api_host_without_http_request(self):
        environment = {"HEFENG_API": API_KEY}

        self.assert_query_rejected_without_http("上海", environment)

    def test_rejects_non_host_api_host_without_http_request(self):
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
                self.assert_query_rejected_without_http("上海", environment)


if __name__ == "__main__":
    unittest.main()
