# -*- coding: utf-8 -*-
"""Knowledge-tool routing helpers for MCP-backed chat workflows."""

from __future__ import annotations

import re
from typing import Mapping, Optional


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


def _has_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle.lower() in text for needle in needles)


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
