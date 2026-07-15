# -*- coding: utf-8 -*-
"""Initial MCP tool routing helpers for chat workflows."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping, Optional


_STRUCTURED_ID_RE = re.compile(r"\b[A-Z]{1,8}-\d{2,6}\b", re.IGNORECASE)

_RAG_HINTS = (
    "景观参数",
    "结构化",
    "景点id",
    "景点 ID",
    "点位id",
    "点位 ID",
    "编号",
    "参数",
    "面积",
    "占地",
    "尺寸",
    "坐标",
    "具体位置",
    "开放时间",
    "运营时间",
    "门票",
    "价格",
    "数据集",
)

_SCENIC_DOMAIN_HINTS = (
    "灵山",
    "灵山胜境",
    "拈花湾",
    "九龙灌浴",
    "梵宫",
    "梵天花海",
    "五印坛城",
)

_COURSE_KB_HINTS = (
    "路线",
    "推荐",
    "游览",
    "讲解",
    "讲解重点",
    "兴趣",
    "喜欢",
    "历史",
    "自然风光",
    "课程",
    "指南",
)

_WEATHER_TOOL_NAME = "query_weather"
_KNOWLEDGE_TOOL_NAMES = ("kb_search", "query_yueshen")
_WEATHER_HINTS = (
    "天气",
    "气温",
    "温度",
    "体感",
    "湿度",
    "下雨",
    "降雨",
    "风力",
    "风速",
)
_FORECAST_HINTS = (
    "今晚",
    "稍后",
    "明天",
    "后天",
    "未来",
    "预报",
    "周末",
    "下周",
    "过几天",
)
_FUTURE_PERIOD_RE = re.compile(r"[一二三四五六七八九十两\d]+天(?:后|内)?")
_CITY_FILLERS = (
    "请问",
    "麻烦",
    "帮我",
    "查询",
    "查一下",
    "看看",
    "现在",
    "当前",
    "实时",
    "今天",
    "今日",
    "此刻",
    "目前",
    "最近",
)
_NON_CITY_WORDS = (
    "什么",
    "什么地方",
    "哪个城市",
    "哪座城市",
    "这里",
    "那里",
    "当地",
    "本地",
    "外面",
    "哪儿",
    "哪里",
)
_CITY_PATTERN = re.compile(r"^[\u4e00-\u9fffA-Za-z·-]{2,30}$")


@dataclass(frozen=True)
class InitialToolContext:
    """Registries used for planning, first-call authorization and execution."""

    mode: str
    planner_tools: dict[str, object]
    allowed_tools: dict[str, object]
    execution_tools: dict[str, object]


def _has_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle.lower() in text for needle in needles)


def _extract_weather_city(user_query: str) -> Optional[str]:
    text = re.sub(r"[\s，。！？、,.!?]", "", user_query or "")
    if not text or _has_any(text, _FORECAST_HINTS) or _FUTURE_PERIOD_RE.search(text):
        return None
    positions = [text.find(hint) for hint in _WEATHER_HINTS if hint in text]
    if not positions:
        return None
    city = text[: min(positions)]
    for filler in _CITY_FILLERS:
        city = city.replace(filler, "")
    if not city or city in _NON_CITY_WORDS or not _CITY_PATTERN.fullmatch(city):
        return None
    return city


def select_weather_tool_candidates(
    tool_registry: Mapping[str, object],
    user_query: str,
) -> dict[str, object]:
    """Return a weather-only registry for explicit current-city questions."""
    if _WEATHER_TOOL_NAME not in tool_registry or not _extract_weather_city(user_query):
        return {}
    return {_WEATHER_TOOL_NAME: tool_registry[_WEATHER_TOOL_NAME]}


def _select_tools(
    tool_registry: Mapping[str, object],
    tool_names: tuple[str, ...],
) -> dict[str, object]:
    return {name: tool_registry[name] for name in tool_names if name in tool_registry}


def select_initial_knowledge_tool(
    tool_registry: Mapping[str, object],
    user_query: str,
    keyword: str = "",
) -> Optional[str]:
    """Choose the first knowledge tool without forcing every query into kb_search."""
    has_course_kb = "kb_search" in tool_registry
    has_rag = "query_yueshen" in tool_registry
    if not has_course_kb and not has_rag:
        return None

    search_text = f"{keyword or ''} {user_query or ''}".strip().lower()
    if has_rag and (_STRUCTURED_ID_RE.search(search_text) or _has_any(search_text, _RAG_HINTS)):
        return "query_yueshen"

    if has_course_kb and _has_any(search_text, _COURSE_KB_HINTS + _SCENIC_DOMAIN_HINTS):
        return "kb_search"

    if has_rag and _has_any(search_text, _SCENIC_DOMAIN_HINTS):
        return "query_yueshen"

    return None


def build_initial_tool_context(
    tool_registry: Mapping[str, object],
    user_query: str,
) -> Optional[InitialToolContext]:
    """Build isolated registries for the first planner and tool call."""
    weather_tools = select_weather_tool_candidates(tool_registry, user_query)
    if weather_tools:
        return InitialToolContext("weather", weather_tools, weather_tools, weather_tools)

    knowledge_tool = select_initial_knowledge_tool(tool_registry, user_query, user_query)
    if not knowledge_tool:
        return None
    knowledge_tools = _select_tools(tool_registry, _KNOWLEDGE_TOOL_NAMES)
    return InitialToolContext(
        "knowledge",
        knowledge_tools,
        knowledge_tools,
        dict(tool_registry),
    )


def resolve_initial_tool_call(
    allowed_tools: Mapping[str, object],
    user_query: str,
    decision: object,
) -> Optional[tuple[str, dict[str, Any]]]:
    """Normalize an allowed explicit call or the legacy knowledge keyword form."""
    if not isinstance(decision, Mapping) or decision.get("action") != "tool":
        return None
    tool_name = decision.get("tool")
    args = decision.get("args")
    if isinstance(tool_name, str):
        if tool_name not in allowed_tools or not isinstance(args, dict):
            return None
        return tool_name, dict(args)

    keyword = decision.get("keyword")
    if not isinstance(keyword, str):
        return None
    search_query = keyword.strip() or (user_query or "").strip()
    knowledge_tool = select_initial_knowledge_tool(allowed_tools, user_query, search_query)
    if not knowledge_tool:
        return None
    normalized_args: dict[str, Any] = {"query": search_query}
    if knowledge_tool == "query_yueshen":
        normalized_args["top_k"] = 3
    return knowledge_tool, normalized_args
