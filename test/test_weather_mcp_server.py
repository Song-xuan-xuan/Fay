from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import asyncio
from contextlib import redirect_stdout
import importlib
import io
import unittest
from unittest.mock import patch

from mcp.types import TextContent


SERVER_PATH = PROJECT_ROOT / "mcp_servers" / "weather" / "server.py"
WEATHER_DIR = SERVER_PATH.parent


def import_weather_server():
    if not SERVER_PATH.exists():
        raise AssertionError(f"天气 MCP 服务不存在: {SERVER_PATH}")
    return importlib.import_module("mcp_servers.weather.server")


class WeatherMcpServerTest(unittest.TestCase):
    def test_list_tools_defines_only_query_weather_contract(self):
        weather_server = import_weather_server()

        tools = asyncio.run(weather_server.handle_list_tools())

        self.assertEqual(1, len(tools))
        tool = tools[0]
        self.assertEqual("query_weather", tool.name)
        self.assertIn("天气", tool.description)
        self.assertIn("城市", tool.description)
        self.assertEqual("object", tool.inputSchema["type"])
        self.assertEqual(
            "string",
            tool.inputSchema["properties"]["city_name"]["type"],
        )
        self.assertEqual(["city_name"], tool.inputSchema["required"])

    def test_query_weather_calls_client_and_wraps_text_content(self):
        weather_server = import_weather_server()
        expected = "北京：晴，温度 28°C"

        with patch.object(
            weather_server.weather_client,
            "query_current_weather",
            return_value=expected,
        ) as query_weather:
            result = asyncio.run(
                weather_server.handle_call_tool(
                    "query_weather",
                    {"city_name": "北京"},
                )
            )

        query_weather.assert_called_once_with("北京")
        self.assertEqual(1, len(result))
        self.assertIsInstance(result[0], TextContent)
        self.assertEqual("text", result[0].type)
        self.assertEqual(expected, result[0].text)

    def test_empty_or_missing_city_is_stably_handled_by_client(self):
        weather_server = import_weather_server()

        for arguments in ({}, {"city_name": ""}, {"city_name": "   "}):
            with self.subTest(arguments=arguments):
                result = asyncio.run(
                    weather_server.handle_call_tool("query_weather", arguments)
                )
                self.assertEqual(1, len(result))
                self.assertIsInstance(result[0], TextContent)
                self.assertEqual("城市名称不能为空", result[0].text)

    def test_unknown_tool_returns_stable_chinese_message(self):
        weather_server = import_weather_server()

        result = asyncio.run(
            weather_server.handle_call_tool("missing_tool", {})
        )

        self.assertEqual(1, len(result))
        self.assertIsInstance(result[0], TextContent)
        self.assertEqual("未知工具: missing_tool", result[0].text)

    def test_direct_import_and_handler_calls_do_not_write_stdout(self):
        if not SERVER_PATH.exists():
            self.fail(f"天气 MCP 服务不存在: {SERVER_PATH}")

        original_path = list(sys.path)
        sys.modules.pop("server", None)
        output = io.StringIO()
        try:
            sys.path.insert(0, str(WEATHER_DIR))
            with redirect_stdout(output):
                direct_server = importlib.import_module("server")
                tools = asyncio.run(direct_server.handle_list_tools())
                with patch.object(
                    direct_server.weather_client,
                    "query_current_weather",
                    return_value="测试天气",
                ):
                    result = asyncio.run(
                        direct_server.handle_call_tool(
                            "query_weather",
                            {"city_name": "北京"},
                        )
                    )
        finally:
            sys.path[:] = original_path
            sys.modules.pop("server", None)

        self.assertEqual("", output.getvalue())
        self.assertEqual("query_weather", tools[0].name)
        self.assertEqual("测试天气", result[0].text)


if __name__ == "__main__":
    unittest.main()
