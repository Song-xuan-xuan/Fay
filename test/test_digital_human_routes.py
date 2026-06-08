import importlib
import io
import json
import os
import unittest

from user_management_test_helpers import TempProjectMixin


class DigitalHumanRoutesTest(TempProjectMixin, unittest.TestCase):
    def setUp(self):
        super().setUp()
        self._previous_config_center_id = os.environ.pop("FAY_CONFIG_CENTER_ID", None)
        self._reset_singletons()
        with open("config.json", "w", encoding="utf-8") as file:
            json.dump(
                {
                    "auth": {
                        "enabled": True,
                        "jwt_expiration_hours": 168,
                        "default_admin_username": "admin",
                        "default_admin_password": "admin123",
                    },
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
                        "contact": "",
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
                    "memory": {"isolate_by_user": True},
                },
                file,
                ensure_ascii=False,
            )

    def tearDown(self):
        if self._previous_config_center_id is not None:
            os.environ["FAY_CONFIG_CENTER_ID"] = self._previous_config_center_id
        super().tearDown()

    def _client(self):
        from core import member_db

        db = member_db.new_instance()
        db.create_default_admin("admin", "admin123")
        flask_server = importlib.import_module("gui.flask_server")
        return getattr(flask_server, "__app").test_client()

    def _admin_headers(self, client):
        response = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
        self.assertEqual(200, response.status_code, response.get_data(as_text=True))
        return {"Authorization": f"Bearer {response.get_json()['token']}"}

    def test_lists_default_digital_human_and_searches_persona(self):
        client = self._client()
        headers = self._admin_headers(client)

        listed = client.get("/api/digital-humans?keyword=工作协助", headers=headers)

        self.assertEqual(200, listed.status_code, listed.get_data(as_text=True))
        payload = listed.get_json()
        self.assertEqual("fay_default", payload["active_id"])
        self.assertEqual(["fay_default"], [item["id"] for item in payload["items"]])
        self.assertEqual("Fay", payload["active"]["name"])

    def test_creates_and_activates_digital_human_without_changing_global_interaction(self):
        client = self._client()
        headers = self._admin_headers(client)

        created = client.post(
            "/api/digital-humans",
            json={
                "name": "讲师",
                "type": "image",
                "cover_url": "/cover/teacher.png",
                "voice": "zh-CN-XiaoyiNeural",
                "tags": ["教培"],
                "persona": {"position": "教培", "goal": "提供知识", "additional": "耐心"},
            },
            headers=headers,
        )
        self.assertEqual(200, created.status_code, created.get_data(as_text=True))
        human_id = created.get_json()["digital_human"]["id"]

        activated = client.post(f"/api/digital-humans/{human_id}/activate", headers=headers)

        self.assertEqual(200, activated.status_code, activated.get_data(as_text=True))
        data_response = client.post("/api/get-data", headers=headers)
        self.assertEqual(200, data_response.status_code, data_response.get_data(as_text=True))
        data = json.loads(data_response.get_data(as_text=True))
        self.assertEqual("讲师", data["config"]["attribute"]["name"])
        self.assertEqual("提供知识", data["config"]["attribute"]["goal"])
        self.assertEqual("hello", data["config"]["source"]["wake_word"])
        self.assertEqual("qa.csv", data["config"]["interact"]["QnA"])
        self.assertEqual(human_id, data["config"]["digital_humans"]["active_id"])

    def test_cover_upload_rejects_non_image_files(self):
        client = self._client()
        headers = self._admin_headers(client)

        uploaded = client.post(
            "/api/digital-humans/fay_default/cover",
            data={"cover": (io.BytesIO(b"not image"), "cover.txt")},
            content_type="multipart/form-data",
            headers=headers,
        )

        self.assertEqual(400, uploaded.status_code, uploaded.get_data(as_text=True))

    def test_cover_upload_rejects_fake_image_with_allowed_extension(self):
        client = self._client()
        headers = self._admin_headers(client)

        uploaded = client.post(
            "/api/digital-humans/fay_default/cover",
            data={"cover": (io.BytesIO(b"not a real png"), "cover.png")},
            content_type="multipart/form-data",
            headers=headers,
        )

        self.assertEqual(400, uploaded.status_code, uploaded.get_data(as_text=True))

    def test_cover_upload_updates_digital_human_cover_url(self):
        client = self._client()
        headers = self._admin_headers(client)

        uploaded = client.post(
            "/api/digital-humans/fay_default/cover",
            data={"cover": (io.BytesIO(b"\x89PNG\r\n\x1a\nfake body"), "cover.png")},
            content_type="multipart/form-data",
            headers=headers,
        )

        self.assertEqual(200, uploaded.status_code, uploaded.get_data(as_text=True))
        payload = uploaded.get_json()
        self.assertTrue(payload["cover_url"].startswith("/digital-humans/covers/fay_default-"))
        self.assertEqual(payload["cover_url"], payload["digital_human"]["cover_url"])

    def test_imports_live2d_resource_models(self):
        client = self._client()
        headers = self._admin_headers(client)

        imported = client.post("/api/digital-humans/import-live2d-resources", headers=headers)

        self.assertEqual(200, imported.status_code, imported.get_data(as_text=True))
        payload = imported.get_json()
        imported_ids = {item["id"] for item in payload["imported"]}
        self.assertIn("live2d_haru", imported_ids)
        self.assertIn("live2d_hiyori", imported_ids)
        self.assertIn("live2d_mao", imported_ids)
        self.assertIn("live2d_natori", imported_ids)

    def test_reads_live2d_resource_cover_file(self):
        client = self._client()

        response = client.get("/digital-humans/live2d-resources/Haru/Haru.2048/texture_00.png")

        self.assertEqual(200, response.status_code, response.status)
        self.assertGreater(len(response.data), 8)
        response.close()


if __name__ == "__main__":
    unittest.main()
