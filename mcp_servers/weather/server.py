#!/usr/bin/env python3
"""通过 stdio 暴露实时天气查询工具。"""

import asyncio
from typing import Any

import mcp.server.stdio
from mcp.server import Server
from mcp.types import CallToolResult, TextContent, Tool

if __package__:
    from . import weather_client
else:
    import weather_client


server = Server("weather")

QUERY_WEATHER_TOOL = Tool(
    name="query_weather",
    description="查询指定城市的当前实时天气，包括温度、湿度、风力和能见度。",
    inputSchema={
        "type": "object",
        "properties": {
            "city_name": {
                "type": "string",
                "minLength": 1,
                "description": "要查询天气的城市名称，例如北京或上海。",
            }
        },
        "required": ["city_name"],
        "additionalProperties": False,
    },
)


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return [QUERY_WEATHER_TOOL]


def _text_result(text: str, *, is_error: bool) -> CallToolResult:
    return CallToolResult(
        content=[TextContent(type="text", text=text)],
        isError=is_error,
    )


@server.call_tool()
async def handle_call_tool(
    name: str,
    arguments: dict[str, Any] | None,
) -> CallToolResult:
    if name != "query_weather":
        return _text_result(f"未知工具: {name}", is_error=True)

    city_name = (arguments or {}).get("city_name", "")
    try:
        summary = await asyncio.to_thread(
            weather_client.query_current_weather,
            city_name,
        )
    except weather_client.WeatherQueryError as exc:
        return _text_result(str(exc), is_error=True)
    except Exception:
        return _text_result("天气查询失败", is_error=True)
    return _text_result(summary, is_error=False)


async def main() -> None:
    async with mcp.server.stdio.stdio_server() as streams:
        read_stream, write_stream = streams
        options = server.create_initialization_options()
        await server.run(read_stream, write_stream, options)


if __name__ == "__main__":
    asyncio.run(main())
