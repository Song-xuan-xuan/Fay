# -*- coding: utf-8 -*-

import sys
import unittest
from pathlib import Path

from flask import Flask

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from gui.vue_spa_routes import register_vue_spa_routes


class VueSpaFallbackTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        register_vue_spa_routes(self.app, lambda: "vue-entry")
        self.client = self.app.test_client()

    def test_app_history_routes_return_vue_entry(self):
        for path in ("/app", "/app/settings", "/app/chat"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(200, response.status_code)
                self.assertEqual("vue-entry", response.get_data(as_text=True))

    def test_fallback_does_not_capture_other_route_families(self):
        for path in ("/api/missing", "/assets/missing", "/Page3"):
            with self.subTest(path=path):
                self.assertEqual(404, self.client.get(path).status_code)

    def test_main_flask_app_registers_spa_routes(self):
        source = (PROJECT_ROOT / "gui" / "flask_server.py").read_text(encoding="utf-8-sig")

        self.assertIn("from gui.vue_spa_routes import register_vue_spa_routes", source)
        self.assertIn("register_vue_spa_routes(__app, __get_vue_app)", source)


if __name__ == "__main__":
    unittest.main()
