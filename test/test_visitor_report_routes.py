import importlib
import json
import os
import sqlite3
import time
import unittest

from user_management_test_helpers import TempProjectMixin


class VisitorReportRoutesTest(TempProjectMixin, unittest.TestCase):
    def _client(self):
        from core import member_db

        db = member_db.new_instance()
        db.create_default_admin('admin', 'admin123')
        flask_server = importlib.import_module('gui.flask_server')
        return getattr(flask_server, '__app').test_client()

    def _admin_headers(self, client):
        response = client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin123'})
        self.assertEqual(200, response.status_code, response.get_data(as_text=True))
        return {'Authorization': f"Bearer {response.get_json()['token']}"}

    def _user_headers(self, client):
        from core import member_db

        user = member_db.new_instance().create_user_with_password('alice', 'alicepass123', role='user')
        response = client.post('/api/auth/login', json={'username': 'alice', 'password': 'alicepass123'})
        self.assertEqual(200, response.status_code, response.get_data(as_text=True))
        return {'Authorization': f"Bearer {response.get_json()['token']}"}, user['uid']

    def _write_messages(self, uid):
        conn = sqlite3.connect(os.path.join('memory', 'fay.db'))
        conn.execute(
            '''CREATE TABLE T_Msg (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT, way TEXT, content TEXT NOT NULL, createtime INTEGER,
                username TEXT, uid INTEGER, images TEXT, session_id INTEGER, topic TEXT
            )'''
        )
        now_ms = int(time.time() * 1000)
        conn.execute(
            '''INSERT INTO T_Msg
            (type, way, content, createtime, username, uid, images, session_id, topic)
            VALUES ('member', 'text', '我要投诉停车场坏了', ?, 'alice', ?, NULL, 1, '')''',
            (now_ms, uid),
        )
        conn.commit()
        conn.close()

    def test_visitor_report_routes_are_admin_only_and_export_report(self):
        client = self._client()
        user_headers, user_uid = self._user_headers(client)
        admin_headers = self._admin_headers(client)
        self._write_messages(user_uid)

        missing = client.get('/api/dashboard/visitor-report/latest')
        denied = client.post('/api/dashboard/visitor-report/generate', json={'range': '7d'}, headers=user_headers)
        generated = client.post('/api/dashboard/visitor-report/generate', json={'range': '7d'}, headers=admin_headers)

        self.assertEqual(401, missing.status_code, missing.get_data(as_text=True))
        self.assertEqual(403, denied.status_code, denied.get_data(as_text=True))
        self.assertEqual(200, generated.status_code, generated.get_data(as_text=True))

        report_id = generated.get_json()['id']
        listed = client.get('/api/dashboard/visitor-report/list', headers=admin_headers)
        detail = client.get(f'/api/dashboard/visitor-report/{report_id}', headers=admin_headers)
        evidence = client.get(f'/api/dashboard/visitor-report/{report_id}/evidence', headers=admin_headers)
        exported = client.get(f'/api/dashboard/visitor-report/{report_id}/export?format=md', headers=admin_headers)

        self.assertEqual(200, listed.status_code, listed.get_data(as_text=True))
        self.assertEqual(1, len(listed.get_json()['items']))
        self.assertEqual(200, detail.status_code, detail.get_data(as_text=True))
        self.assertEqual(200, evidence.status_code, evidence.get_data(as_text=True))
        self.assertIn('我要投诉', json.dumps(evidence.get_json(), ensure_ascii=False))
        self.assertEqual(200, exported.status_code, exported.get_data(as_text=True))
        self.assertIn('# 游客感受度报告', exported.get_data(as_text=True))
        self.assertIn('text/markdown', exported.content_type)

        action_id = detail.get_json()['actions'][0]['id']
        user_denied_requests = [
            client.get('/api/dashboard/visitor-report/list', headers=user_headers),
            client.get(f'/api/dashboard/visitor-report/{report_id}', headers=user_headers),
            client.get(f'/api/dashboard/visitor-report/{report_id}/evidence', headers=user_headers),
            client.get(f'/api/dashboard/visitor-report/{report_id}/export?format=md', headers=user_headers),
            client.post(f'/api/dashboard/visitor-report/action/{action_id}/status', json={'status': 'done'}, headers=user_headers),
        ]
        for response in user_denied_requests:
            self.assertEqual(403, response.status_code, response.get_data(as_text=True))

        updated = client.post(
            f'/api/dashboard/visitor-report/action/{action_id}/status',
            json={'status': 'done'},
            headers=admin_headers,
        )
        self.assertEqual(200, updated.status_code, updated.get_data(as_text=True))
        self.assertEqual('done', updated.get_json()['status'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
