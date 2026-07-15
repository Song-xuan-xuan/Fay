# -*- coding: utf-8 -*-

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from llm.mcp_tool_routing import (
    build_initial_tool_context,
    resolve_initial_tool_call,
    select_initial_knowledge_tool,
    select_weather_tool_candidates,
)


class McpToolRoutingTests(unittest.TestCase):
    def setUp(self):
        self.weather_tool = object()
        self.course_tool = object()
        self.rag_tool = object()
        self.schedule_tool = object()

    def test_existing_knowledge_routing_is_preserved(self):
        registry = {
            "kb_search": self.course_tool,
            "query_yueshen": self.rag_tool,
        }

        self.assertEqual(
            "query_yueshen",
            select_initial_knowledge_tool(registry, "梵宫的开放时间是什么"),
        )
        self.assertEqual(
            "kb_search",
            select_initial_knowledge_tool(registry, "推荐一条拈花湾游览路线"),
        )

    def test_weather_candidates_require_registered_tool_and_explicit_city(self):
        registry = {"query_weather": self.weather_tool}

        self.assertEqual(
            {"query_weather": self.weather_tool},
            select_weather_tool_candidates(registry, "北京现在天气怎么样"),
        )
        self.assertEqual(
            {"query_weather": self.weather_tool},
            select_weather_tool_candidates(registry, "上海气温多少"),
        )
        self.assertEqual({}, select_weather_tool_candidates({}, "北京天气怎么样"))
        self.assertEqual({}, select_weather_tool_candidates(registry, "现在天气怎么样"))

    def test_weather_candidates_reject_ordinary_chat_and_follow_ups(self):
        registry = {"query_weather": self.weather_tool}

        for query in (
            "你好",
            "帮我写一首诗",
            "什么天气适合跑步",
            "最近天气怎么样",
            "上海呢",
            "那里现在怎么样",
        ):
            with self.subTest(query=query):
                self.assertEqual({}, select_weather_tool_candidates(registry, query))

    def test_weather_candidates_reject_future_periods(self):
        registry = {"query_weather": self.weather_tool}

        for query in (
            "北京今晚天气怎么样",
            "北京明天天气怎么样",
            "上海稍后会下雨吗",
            "广州三天天气预报",
            "深圳过几天天气如何",
        ):
            with self.subTest(query=query):
                self.assertEqual({}, select_weather_tool_candidates(registry, query))

    def test_weather_context_isolates_unrelated_tools(self):
        registry = {
            "query_weather": self.weather_tool,
            "kb_search": self.course_tool,
            "schedule_create": self.schedule_tool,
        }

        context = build_initial_tool_context(registry, "北京今天气温多少")

        self.assertIsNotNone(context)
        self.assertEqual("weather", context.mode)
        self.assertEqual({"query_weather"}, set(context.planner_tools))
        self.assertEqual({"query_weather"}, set(context.allowed_tools))
        self.assertEqual({"query_weather"}, set(context.execution_tools))

    def test_knowledge_context_limits_first_call_but_preserves_execution_tools(self):
        registry = {
            "kb_search": self.course_tool,
            "query_yueshen": self.rag_tool,
            "schedule_create": self.schedule_tool,
        }

        context = build_initial_tool_context(registry, "推荐一条拈花湾游览路线")

        self.assertIsNotNone(context)
        self.assertEqual("knowledge", context.mode)
        self.assertEqual({"kb_search", "query_yueshen"}, set(context.planner_tools))
        self.assertEqual({"kb_search", "query_yueshen"}, set(context.allowed_tools))
        self.assertEqual(set(registry), set(context.execution_tools))

    def test_no_context_for_weather_question_without_city(self):
        context = build_initial_tool_context(
            {"query_weather": self.weather_tool},
            "现在天气怎么样",
        )

        self.assertIsNone(context)

    def test_resolves_explicit_weather_tool_and_args(self):
        allowed = {"query_weather": self.weather_tool}
        decision = {
            "action": "tool",
            "tool": "query_weather",
            "args": {"city_name": "北京"},
        }

        self.assertEqual(
            ("query_weather", {"city_name": "北京"}),
            resolve_initial_tool_call(allowed, "北京天气怎么样", decision),
        )

    def test_resolves_explicit_knowledge_tool_and_args(self):
        allowed = {"kb_search": self.course_tool}
        decision = {
            "action": "tool",
            "tool": "kb_search",
            "args": {"query": "拈花湾路线"},
        }

        self.assertEqual(
            ("kb_search", {"query": "拈花湾路线"}),
            resolve_initial_tool_call(allowed, "推荐路线", decision),
        )

    def test_resolves_legacy_keyword_and_yueshen_top_k(self):
        allowed = {"query_yueshen": self.rag_tool}
        decision = {"action": "tool", "keyword": "梵宫开放时间"}

        self.assertEqual(
            ("query_yueshen", {"query": "梵宫开放时间", "top_k": 3}),
            resolve_initial_tool_call(allowed, "梵宫开放时间是什么", decision),
        )

    def test_rejects_unknown_unallowed_and_non_dict_args(self):
        allowed = {"query_weather": self.weather_tool}
        rejected = (
            {"action": "tool", "tool": "unknown", "args": {}},
            {"action": "tool", "tool": "schedule_create", "args": {}},
            {"action": "tool", "tool": "query_weather", "args": "北京"},
            {"action": "finish", "tool": "query_weather", "args": {}},
            "not a decision",
        )

        for decision in rejected:
            with self.subTest(decision=decision):
                self.assertIsNone(
                    resolve_initial_tool_call(allowed, "北京天气怎么样", decision)
                )


if __name__ == "__main__":
    unittest.main()
