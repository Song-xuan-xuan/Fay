import copy
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core import digital_human_service
from utils import config_util


BASE_CONFIG = {
    "attribute": {
        "name": "Fay",
        "voice": "zh-CN-YunxiNeural",
        "goal": "工作协助",
    },
    "digital_humans": {
        "active_id": "fay_default",
        "items": [
            {
                "id": "fay_default",
                "name": "Fay",
                "type": "live2d",
                "cover_url": "/static/images/Normal.gif",
                "render_url": "http://127.0.0.1:5174",
                "voice": "zh-CN-YunxiNeural",
                "tags": [],
                "persona": {"goal": "工作协助"},
                "enabled": True,
                "created_at": "2026-01-01T00:00:00",
                "updated_at": "2026-01-01T00:00:00",
            }
        ],
    },
    "source": {"record": {"enabled": True}},
    "interact": {"playSound": False},
}


class ConfigPersistenceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.tmp.name, "config.json")
        self.previous_config = config_util.config
        self.previous_path = config_util.config_json_path
        config_util.config_json_path = self.config_path
        self._write_config(BASE_CONFIG)

    def tearDown(self):
        config_util.config = self.previous_config
        config_util.config_json_path = self.previous_path
        self.tmp.cleanup()

    def _write_config(self, data):
        with open(self.config_path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    def _read_config(self):
        with open(self.config_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def test_digital_human_persist_preserves_unrelated_disk_changes(self):
        stale = copy.deepcopy(BASE_CONFIG)
        disk = copy.deepcopy(BASE_CONFIG)
        disk["source"]["record"]["enabled"] = False
        self._write_config(disk)
        config_util.config = stale
        stale["digital_humans"]["items"].append({
            "id": "new_human",
            "name": "新数字人",
            "type": "image",
            "cover_url": "/cover.png",
            "render_url": "",
            "voice": "",
            "tags": [],
            "persona": {},
            "enabled": True,
            "created_at": "2026-01-01T00:00:00",
            "updated_at": "2026-01-01T00:00:00",
        })

        with patch.object(config_util, "load_config", return_value={"config": stale}):
            digital_human_service.persist_config(stale, sections=("digital_humans",))

        saved = self._read_config()
        self.assertFalse(saved["source"]["record"]["enabled"])
        self.assertTrue(any(item["id"] == "new_human" for item in saved["digital_humans"]["items"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
