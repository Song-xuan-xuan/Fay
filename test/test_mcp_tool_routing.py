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

    def test_structured_spot_id_questions_prefer_rag(self):
        registry = {"kb_search": self.course_tool, "query_yueshen": self.rag_tool}

        result = select_initial_knowledge_tool(
            registry,
            "拈花湾禅意小镇 这个景点ID为NH-001的具体位置是什么？",
            "NH-001 拈花湾禅意小镇 具体位置",
        )

        self.assertEqual("query_yueshen", result)

    def test_landscape_parameter_questions_prefer_rag(self):
        registry = {"kb_search": self.course_tool, "query_yueshen": self.rag_tool}

        result = select_initial_knowledge_tool(
            registry,
            "我想知道拈花湾禅意小镇的梵天花海的景观参数",
            "梵天花海 景观参数",
        )

        self.assertEqual("query_yueshen", result)

    def test_tour_route_questions_keep_course_kb(self):
        registry = {"kb_search": self.course_tool, "query_yueshen": self.rag_tool}

        result = select_initial_knowledge_tool(
            registry,
            "我喜欢自然风光，帮我推荐灵山胜境的游览路线",
            "自然风光 灵山胜境 游览路线",
        )

        self.assertEqual("kb_search", result)

    def test_scenic_domain_questions_use_course_kb_when_available(self):
        registry = {"kb_search": self.course_tool, "query_yueshen": self.rag_tool}

        result = select_initial_knowledge_tool(
            registry,
            "灵山胜境有什么看点？",
            "灵山胜境 看点",
        )

        self.assertEqual("kb_search", result)

    def test_rag_is_used_when_course_kb_is_unavailable(self):
        result = select_initial_knowledge_tool(
            {"query_yueshen": self.rag_tool},
            "查询梵天花海的景观参数",
            "梵天花海 景观参数",
        )

        self.assertEqual("query_yueshen", result)

    def test_general_questions_do_not_use_knowledge_tools_by_default(self):
        registry = {"kb_search": self.course_tool, "query_yueshen": self.rag_tool}

        result = select_initial_knowledge_tool(
            registry,
            "帮我解释一下 Python 的装饰器是什么",
            "Python 装饰器",
        )

        self.assertIsNone(result)

    def test_general_questions_do_not_fallback_to_rag(self):
        result = select_initial_knowledge_tool(
            {"query_yueshen": self.rag_tool},
            "帮我写一段欢迎词",
            "欢迎词",
        )

        self.assertIsNone(result)

    def test_general_questions_do_not_fallback_to_rag_when_only_rag_available(self):
        result = select_initial_knowledge_tool(
            {"query_yueshen": self.rag_tool},
            "帮我写一段欢迎词",
            "欢迎词",
        )

        self.assertIsNone(result)

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
