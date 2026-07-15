from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import asyncio
from contextlib import redirect_stdout
import importlib
import io
import unittest
from unittest.mock import AsyncMock, patch

from mcp.types import CallToolRequest, CallToolResult, ServerResult, TextContent


SERVER_PATH = PROJECT_ROOT / "mcp_servers" / "weather" / "server.py"
WEATHER_DIR = SERVER_PATH.parent
README_PATH = WEATHER_DIR / "README.md"


def import_weather_server():
    if not SERVER_PATH.exists():
        raise AssertionError(f"天气 MCP 服务不存在: {SERVER_PATH}")
    return importlib.import_module("mcp_servers.weather.server")


class WeatherMcpServerTest(unittest.TestCase):
    def assert_call_result(self, result, *, is_error, text):
        self.assertIsInstance(result, CallToolResult)
        self.assertEqual(is_error, result.isError)
        self.assertEqual(1, len(result.content))
        self.assertIsInstance(result.content[0], TextContent)
        self.assertEqual("text", result.content[0].type)
        self.assertEqual(text, result.content[0].text)

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
        self.assertEqual(
            1,
            tool.inputSchema["properties"]["city_name"].get("minLength"),
        )
        self.assertIs(False, tool.inputSchema.get("additionalProperties"))

    def test_query_weather_calls_client_via_thread_and_returns_success(self):
        weather_server = import_weather_server()
        expected = "北京：晴，温度 28°C"

        to_thread = AsyncMock(return_value=expected)
        with patch.object(weather_server.asyncio, "to_thread", to_thread):
            result = asyncio.run(
                weather_server.handle_call_tool(
                    "query_weather",
                    {"city_name": "北京"},
                )
            )

        to_thread.assert_awaited_once_with(
            weather_server.weather_client.query_current_weather,
            "北京",
        )
        self.assert_call_result(result, is_error=False, text=expected)

    def test_empty_or_missing_city_is_stably_handled_by_client(self):
        weather_server = import_weather_server()

        for arguments in ({}, {"city_name": ""}, {"city_name": "   "}):
            with self.subTest(arguments=arguments):
                result = asyncio.run(
                    weather_server.handle_call_tool("query_weather", arguments)
                )
                self.assert_call_result(
                    result,
                    is_error=True,
                    text="城市名称不能为空",
                )

    def test_unknown_tool_returns_stable_chinese_message(self):
        weather_server = import_weather_server()

        result = asyncio.run(
            weather_server.handle_call_tool("missing_tool", {})
        )

        self.assert_call_result(
            result,
            is_error=True,
            text="未知工具: missing_tool",
        )

    def test_weather_query_error_returns_error_result(self):
        weather_server = import_weather_server()
        to_thread = AsyncMock(
            side_effect=weather_server.weather_client.WeatherQueryError(
                "天气服务认证失败"
            )
        )

        with patch.object(weather_server.asyncio, "to_thread", to_thread):
            result = asyncio.run(
                weather_server.handle_call_tool(
                    "query_weather",
                    {"city_name": "北京"},
                )
            )

        self.assert_call_result(
            result,
            is_error=True,
            text="天气服务认证失败",
        )

    def test_unexpected_error_returns_stable_error_result(self):
        weather_server = import_weather_server()
        to_thread = AsyncMock(side_effect=RuntimeError("sensitive details"))

        with patch.object(weather_server.asyncio, "to_thread", to_thread):
            result = asyncio.run(
                weather_server.handle_call_tool(
                    "query_weather",
                    {"city_name": "北京"},
                )
            )

        self.assert_call_result(
            result,
            is_error=True,
            text="天气查询失败",
        )

    def test_registered_handler_returns_protocol_success_result(self):
        weather_server = import_weather_server()
        request = CallToolRequest(
            params={
                "name": "query_weather",
                "arguments": {"city_name": "北京"},
            }
        )
        handler = weather_server.server.request_handlers[CallToolRequest]
        to_thread = AsyncMock(return_value="协议天气")

        with patch.object(weather_server.asyncio, "to_thread", to_thread):
            response = asyncio.run(handler(request))

        self.assertIsInstance(response, ServerResult)
        self.assert_call_result(
            response.root,
            is_error=False,
            text="协议天气",
        )

    def test_registered_handler_preserves_protocol_error_result(self):
        weather_server = import_weather_server()
        request = CallToolRequest(
            params={
                "name": "query_weather",
                "arguments": {"city_name": "北京"},
            }
        )
        handler = weather_server.server.request_handlers[CallToolRequest]
        to_thread = AsyncMock(
            side_effect=weather_server.weather_client.WeatherQueryError(
                "天气服务配额已用尽"
            )
        )

        with patch.object(weather_server.asyncio, "to_thread", to_thread):
            response = asyncio.run(handler(request))

        self.assertIsInstance(response, ServerResult)
        self.assert_call_result(
            response.root,
            is_error=True,
            text="天气服务配额已用尽",
        )

    def test_import_fallback_does_not_catch_dependency_import_errors(self):
        source = SERVER_PATH.read_text(encoding="utf-8")

        self.assertIn("if __package__:", source)
        self.assertNotIn("except ImportError", source)

    def test_readme_uses_plain_args_and_json_environment_object(self):
        readme = README_PATH.read_text(encoding="utf-8")

        self.assertIn("args：`mcp_servers/weather/server.py`", readme)
        self.assertNotIn('["mcp_servers/weather/server.py"]', readme)
        self.assertIn('"HEFENG_API": "<your-api-key>"', readme)
        self.assertIn('"HEFENG_API_HOST": "<your-api-host>"', readme)

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
                to_thread = AsyncMock(return_value="测试天气")
                with patch.object(direct_server.asyncio, "to_thread", to_thread):
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
        self.assert_call_result(
            result,
            is_error=False,
            text="测试天气",
        )


if __name__ == "__main__":
    unittest.main()
