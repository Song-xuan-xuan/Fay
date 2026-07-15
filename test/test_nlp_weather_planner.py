# -*- coding: utf-8 -*-

import sys
import types
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _install_import_stubs():
    import utils

    util = types.ModuleType("utils.util")
    util.log = lambda *args, **kwargs: None
    util.__getattr__ = lambda name: (lambda *args, **kwargs: None)

    config = types.ModuleType("utils.config_util")
    config.load_config = lambda: None
    config.config = {}
    config.gpt_model_engine = "test-model"
    config.gpt_base_url = "http://127.0.0.1:1/v1"
    config.key_gpt_api_key = "test-key"
    config.big_model_engine = ""
    config.big_model_base_url = ""
    config.big_model_api_key = ""
    config.__getattr__ = lambda name: ""

    sys.modules["utils.util"] = util
    sys.modules["utils.config_util"] = config
    utils.util = util
    utils.config_util = config
    for name in ("core.content_db", "core.stream_manager", "core.member_db"):
        sys.modules[name] = types.ModuleType(name)


_install_import_stubs()

from llm.mcp_tool_routing import InitialToolContext
from llm.nlp_cognitive_stream import (
    WorkflowToolSpec,
    _build_initial_execution_state,
    _build_planner_messages,
)


def _tool_spec(name, description, schema):
    return WorkflowToolSpec(
        name=name,
        description=description,
        schema=schema,
        executor=lambda args, attempt: (True, "ok", None),
        example_args={"city_name": "北京"} if name == "query_weather" else {},
    )


class WeatherPlannerTests(unittest.TestCase):
    def setUp(self):
        self.weather = _tool_spec(
            "query_weather",
            "查询指定城市的实时天气",
            {
                "type": "object",
                "properties": {
                    "city_name": {"type": "string", "description": "城市名称"}
                },
                "required": ["city_name"],
            },
        )
        self.schedule = _tool_spec("schedule_create", "创建日程", {"type": "object"})
        self.knowledge = _tool_spec("kb_search", "查询课程知识库", {"type": "object"})

    def test_weather_prompt_contains_schema_contract_and_only_weather_tool(self):
        state = {
            "request": "北京现在天气怎么样",
            "messages": [],
            "tool_results": [],
            "context": {
                "tool_mode": "weather",
                "tool_registry": {"query_weather": self.weather},
                "system_prompt": "你是 Fay。",
            },
        }

        prompt = _build_planner_messages(state)[0].content

        self.assertIn("查询指定城市的实时天气", prompt)
        self.assertIn("city_name (string，必填)", prompt)
        self.assertIn('{"action": "tool", "tool": "query_weather", "args":', prompt)
        self.assertIn("没有明确城市", prompt)
        self.assertNotIn("schedule_create", prompt)
        self.assertNotIn('"keyword"', prompt)

    def test_knowledge_prompt_keeps_legacy_keyword_contract(self):
        state = {
            "request": "推荐一条拈花湾路线",
            "messages": [],
            "tool_results": [],
            "context": {
                "tool_mode": "knowledge",
                "tool_registry": {"kb_search": self.knowledge},
            },
        }

        prompt = _build_planner_messages(state)[0].content

        self.assertIn('{"action": "tool", "keyword":', prompt)
        self.assertNotIn("city_name", prompt)
        self.assertNotIn("查询指定城市的实时天气", prompt)

    def test_builds_weather_execution_state_with_isolated_registry(self):
        context = InitialToolContext(
            "weather",
            {"query_weather": self.weather},
            {"query_weather": self.weather},
            {"query_weather": self.weather},
        )

        state = _build_initial_execution_state(
            self._base_context(),
            context,
            ("query_weather", {"city_name": "北京"}),
        )

        self.assertEqual(
            {"name": "query_weather", "args": {"city_name": "北京"}},
            state.first_plan,
        )
        self.assertEqual({"query_weather"}, set(state.tool_registry))

    def test_knowledge_state_preserves_full_execution_registry(self):
        context = InitialToolContext(
            "knowledge",
            {"kb_search": self.knowledge},
            {"kb_search": self.knowledge},
            {"kb_search": self.knowledge, "schedule_create": self.schedule},
        )

        state = _build_initial_execution_state(
            self._base_context(),
            context,
            ("kb_search", {"query": "拈花湾路线"}),
        )

        self.assertEqual("kb_search", state.first_plan["name"])
        self.assertEqual({"kb_search", "schedule_create"}, set(state.tool_registry))

    def test_legacy_yueshen_call_keeps_top_k(self):
        context = InitialToolContext(
            "knowledge",
            {},
            {},
            {"query_yueshen": self.knowledge},
        )

        state = _build_initial_execution_state(
            self._base_context(),
            context,
            ("query_yueshen", {"query": "梵宫开放时间", "top_k": 3}),
        )

        self.assertEqual(3, state.first_plan["args"]["top_k"])

    def test_does_not_build_state_without_context_or_resolved_call(self):
        base = self._base_context()
        context = InitialToolContext("weather", {}, {}, {})

        self.assertIsNone(_build_initial_execution_state(base, None, None))
        self.assertIsNone(_build_initial_execution_state(base, context, None))

    @staticmethod
    def _base_context():
        return {
            "username": "tester",
            "conversation_id": "conversation-1",
            "original_request": "北京现在天气怎么样",
            "system_prompt": "你是 Fay。",
            "messages_buffer": [{"role": "user", "content": "测试"}],
            "memory_context": "",
            "observation": None,
            "prestart_context": "",
            "on_complete": None,
        }


if __name__ == "__main__":
    unittest.main()
