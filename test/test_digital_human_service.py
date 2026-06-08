import copy
import json
import os
import tempfile
import sys
import unittest
from unittest.mock import patch


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


BASE_CONFIG = {
    "attribute": {
        "name": "Fay",
        "gender": "男",
        "age": "成年",
        "birth": "Github",
        "zodiac": "蛇",
        "constellation": "水瓶座",
        "position": "陪伴",
        "goal": "工作协助",
        "job": "助理",
        "contact": "qq467665317",
        "additional": "发呆",
        "voice": "zh-CN-YunxiNeural",
    },
    "source": {
        "wake_word": "hello",
        "wake_word_enabled": True,
    },
    "interact": {
        "QnA": "qa.csv",
        "playSound": False,
    },
    "memory": {
        "isolate_by_user": True,
    },
}


class DigitalHumanServiceTest(unittest.TestCase):
    def setUp(self):
        from utils import config_util

        self.config_util = config_util
        self.saved = []
        self.config_util.config = copy.deepcopy(BASE_CONFIG)
        self.config_util.config_json_path = "config.json"

    def _patch_config_io(self):
        return patch.multiple(
            self.config_util,
            save_config=lambda data: self.saved.append(copy.deepcopy(data)),
            load_config=lambda force_reload=False: {"config": self.config_util.config},
        )

    def test_migrates_existing_attribute_to_default_digital_human(self):
        from core import digital_human_service as service

        config = copy.deepcopy(BASE_CONFIG)
        result = service.ensure_digital_humans_config(config)

        self.assertEqual("fay_default", result["digital_humans"]["active_id"])
        self.assertEqual(1, len(result["digital_humans"]["items"]))
        human = result["digital_humans"]["items"][0]
        self.assertEqual("Fay", human["name"])
        self.assertEqual("live2d", human["type"])
        self.assertEqual("zh-CN-YunxiNeural", human["voice"])
        self.assertEqual("工作协助", human["persona"]["goal"])
        self.assertNotIn("wake_word", human["persona"])
        self.assertNotIn("QnA", human["persona"])

    def test_search_matches_name_tags_voice_and_persona_fields(self):
        from core import digital_human_service as service

        self.config_util.config["digital_humans"] = {
            "active_id": "sales",
            "items": [
                {
                    "id": "sales",
                    "name": "销售顾问",
                    "type": "iframe",
                    "cover_url": "/cover/sales.png",
                    "render_url": "http://127.0.0.1:7001",
                    "voice": "温柔女声",
                    "tags": ["销售", "活泼"],
                    "persona": {"position": "销售", "goal": "促成交易", "additional": "热情"},
                    "enabled": True,
                },
                {
                    "id": "support",
                    "name": "客服助手",
                    "type": "image",
                    "cover_url": "/cover/support.gif",
                    "render_url": "",
                    "voice": "稳重男声",
                    "tags": ["客服"],
                    "persona": {"position": "客服", "goal": "解决问题", "additional": "沉稳"},
                    "enabled": True,
                },
            ],
        }

        self.assertEqual(["sales"], [item["id"] for item in service.list_digital_humans("活泼 女声")])
        self.assertEqual(["support"], [item["id"] for item in service.list_digital_humans("解决问题")])
        self.assertEqual(["sales"], [item["id"] for item in service.list_digital_humans(human_type="iframe")])

    def test_activate_updates_active_id_and_runtime_attribute_only(self):
        from core import digital_human_service as service

        self.config_util.config = copy.deepcopy(BASE_CONFIG)
        self.config_util.config["digital_humans"] = {
            "active_id": "fay_default",
            "items": [
                {
                    "id": "fay_default",
                    "name": "Fay",
                    "type": "live2d",
                    "cover_url": "",
                    "render_url": "http://127.0.0.1:5174",
                    "voice": "zh-CN-YunxiNeural",
                    "tags": [],
                    "persona": {"goal": "工作协助", "position": "陪伴"},
                    "enabled": True,
                },
                {
                    "id": "teacher",
                    "name": "讲师",
                    "type": "image",
                    "cover_url": "/cover/teacher.png",
                    "render_url": "",
                    "voice": "zh-CN-XiaoyiNeural",
                    "tags": ["教培"],
                    "persona": {"goal": "提供知识", "position": "教培", "additional": "耐心"},
                    "enabled": True,
                },
            ],
        }
        original_source = copy.deepcopy(self.config_util.config["source"])
        original_interact = copy.deepcopy(self.config_util.config["interact"])
        original_memory = copy.deepcopy(self.config_util.config["memory"])

        with self._patch_config_io():
            active = service.activate_digital_human("teacher")

        self.assertEqual("teacher", active["id"])
        self.assertEqual("teacher", self.config_util.config["digital_humans"]["active_id"])
        self.assertEqual("讲师", self.config_util.config["attribute"]["name"])
        self.assertEqual("zh-CN-XiaoyiNeural", self.config_util.config["attribute"]["voice"])
        self.assertEqual("提供知识", self.config_util.config["attribute"]["goal"])
        self.assertEqual(original_source, self.config_util.config["source"])
        self.assertEqual(original_interact, self.config_util.config["interact"])
        self.assertEqual(original_memory, self.config_util.config["memory"])
        self.assertEqual(1, len(self.saved))

    def test_delete_rejects_active_human(self):
        from core import digital_human_service as service

        service.ensure_digital_humans_config(self.config_util.config)

        with self.assertRaises(ValueError):
            service.delete_digital_human("fay_default", persist=False)

    def test_syncs_runtime_attribute_back_to_active_human(self):
        from core import digital_human_service as service

        service.ensure_digital_humans_config(self.config_util.config)
        self.config_util.config["attribute"]["name"] = "新 Fay"
        self.config_util.config["attribute"]["voice"] = "zh-CN-XiaoxiaoNeural"
        self.config_util.config["attribute"]["goal"] = "陪伴情感"

        service.sync_active_human_from_attribute(self.config_util.config)
        human = service.get_active_digital_human()

        self.assertEqual("新 Fay", human["name"])
        self.assertEqual("zh-CN-XiaoxiaoNeural", human["voice"])
        self.assertEqual("陪伴情感", human["persona"]["goal"])
        self.assertNotIn("wake_word", human["persona"])

    def test_discovers_live2d_resource_models(self):
        from core import live2d_resource_service as service

        with tempfile.TemporaryDirectory() as temp_dir:
            resources = os.path.join(temp_dir, "Resources", "Haru", "Haru.2048")
            os.makedirs(resources)
            with open(os.path.join(temp_dir, "Resources", "Haru", "Haru.model3.json"), "w", encoding="utf-8") as file:
                json.dump({"FileReferences": {"Moc": "Haru.moc3"}}, file)
            with open(os.path.join(resources, "texture_00.png"), "wb") as file:
                file.write(b"\x89PNG\r\n\x1a\n")

            models = service.discover_live2d_resource_models(temp_dir, "http://127.0.0.1:5174")

        self.assertEqual(1, len(models))
        self.assertEqual("Haru", models[0]["model_name"])
        self.assertEqual("live2d_haru", models[0]["id"])
        self.assertEqual("http://127.0.0.1:5174?model=Haru", models[0]["render_url"])
        self.assertEqual("/digital-humans/live2d-resources/Haru/Haru.2048/texture_00.png", models[0]["cover_url"])

    def test_imports_live2d_resource_models_without_duplicates(self):
        from core import live2d_resource_service as service

        with tempfile.TemporaryDirectory() as temp_dir:
            model_dir = os.path.join(temp_dir, "Resources", "Mao")
            os.makedirs(model_dir)
            with open(os.path.join(model_dir, "Mao.model3.json"), "w", encoding="utf-8") as file:
                json.dump({"FileReferences": {"Moc": "Mao.moc3"}}, file)

            with self._patch_config_io():
                first = service.import_live2d_resource_models(temp_dir, "http://127.0.0.1:5174")
                second = service.import_live2d_resource_models(temp_dir, "http://127.0.0.1:5174")

        self.assertEqual(["live2d_mao"], [item["id"] for item in first["imported"]])
        self.assertEqual([], second["imported"])
        self.assertEqual(1, len([item for item in self.config_util.config["digital_humans"]["items"] if item["id"] == "live2d_mao"]))
        self.assertEqual("http://127.0.0.1:5174?model=Mao", self.config_util.config["digital_humans"]["items"][-1]["render_url"])


if __name__ == "__main__":
    unittest.main()
