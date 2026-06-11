import importlib
import io
import json
import os
import sqlite3
import unittest

from user_management_test_helpers import TempProjectMixin


class TourismRecommendationRoutesTest(TempProjectMixin, unittest.TestCase):
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

        user = member_db.new_instance().create_user_with_password('alice', 'alicepass123', role='user', force_change=False)
        response = client.post('/api/auth/login', json={'username': 'alice', 'password': 'alicepass123'})
        self.assertEqual(200, response.status_code, response.get_data(as_text=True))
        return {'Authorization': f"Bearer {response.get_json()['token']}"}, user['uid']

    def test_user_recommendation_flow_requires_login(self):
        client = self._client()
        admin_headers = self._admin_headers(client)
        user_headers, user_uid = self._user_headers(client)
        self._seed_admin_route(client, admin_headers)

        missing = client.post('/api/recommendation/recommend', json={'interests': ['history']})
        saved = client.put('/api/recommendation/preferences', json={'interests': ['history']}, headers=user_headers)
        recommended = client.post(
            '/api/recommendation/recommend',
            json={'interests': ['history'], 'time_budget_minutes': 120},
            headers=user_headers,
        )

        self.assertEqual(401, missing.status_code, missing.get_data(as_text=True))
        self.assertEqual(200, saved.status_code, saved.get_data(as_text=True))
        self.assertEqual(user_uid, saved.get_json()['preferences']['user_id'])
        self.assertEqual(200, recommended.status_code, recommended.get_data(as_text=True))
        self.assertEqual('历史文化半日线', recommended.get_json()['main_route']['name'])

        history = client.get('/api/recommendation/history', headers=user_headers)
        detail = client.get(f"/api/recommendation/history/{recommended.get_json()['recommendation_id']}", headers=user_headers)
        feedback = client.post(
            '/api/recommendation/feedback',
            json={'recommendation_id': recommended.get_json()['recommendation_id'], 'action': 'adopt', 'rating': 5},
            headers=user_headers,
        )

        self.assertEqual(200, history.status_code, history.get_data(as_text=True))
        self.assertEqual(1, len(history.get_json()['items']))
        self.assertEqual(200, detail.status_code, detail.get_data(as_text=True))
        self.assertEqual(200, feedback.status_code, feedback.get_data(as_text=True))
        self.assertEqual('adopt', feedback.get_json()['feedback']['action'])

    def test_recommendation_requires_login_when_global_auth_is_disabled(self):
        self._set_global_auth(False)
        client = self._client()

        user_entry = client.post('/api/recommendation/recommend', json={'interests': ['history']})
        admin_entry = client.post('/api/recommendation/admin/attractions', json={'name': '古城墙'})

        self.assertEqual(401, user_entry.status_code, user_entry.get_data(as_text=True))
        self.assertEqual(401, admin_entry.status_code, admin_entry.get_data(as_text=True))

    def test_admin_maintenance_routes_are_admin_only(self):
        client = self._client()
        user_headers, _ = self._user_headers(client)
        admin_headers = self._admin_headers(client)

        denied = client.post('/api/recommendation/admin/attractions', json={'name': '古城墙'}, headers=user_headers)
        created = client.post(
            '/api/recommendation/admin/attractions',
            json={'name': '古城墙', 'category': '历史遗迹', 'tags': ['history']},
            headers=admin_headers,
        )

        self.assertEqual(403, denied.status_code, denied.get_data(as_text=True))
        self.assertEqual(200, created.status_code, created.get_data(as_text=True))
        attraction_id = created.get_json()['id']

        template = client.post(
            '/api/recommendation/admin/templates',
            json={'name': '历史文化半日线', 'interest_tags': ['history'], 'duration_minutes': 120},
            headers=admin_headers,
        )
        stop = client.post(
            f"/api/recommendation/admin/templates/{template.get_json()['id']}/stops",
            json={'attraction_id': attraction_id, 'order_index': 1, 'stay_minutes': 35},
            headers=admin_headers,
        )
        material = client.post(
            '/api/recommendation/admin/materials',
            json={'attraction_id': attraction_id, 'interest_tag': 'history', 'title': '城墙讲解', 'script': '讲述建城背景。'},
            headers=admin_headers,
        )
        edge_walk_minutes = self._exercise_edge_routes(client, admin_headers, attraction_id)
        config = client.put('/api/recommendation/admin/config', json={'weights': {'interest_match': 0.6}}, headers=admin_headers)
        listed = client.get('/api/recommendation/admin/attractions', headers=admin_headers)

        self.assertEqual(200, template.status_code, template.get_data(as_text=True))
        self.assertEqual(200, stop.status_code, stop.get_data(as_text=True))
        self.assertEqual(200, material.status_code, material.get_data(as_text=True))
        self.assertEqual(200, config.status_code, config.get_data(as_text=True))
        self.assertEqual(200, listed.status_code, listed.get_data(as_text=True))
        self.assertEqual('古城墙', listed.get_json()['items'][0]['name'])
        self.assertEqual(6, edge_walk_minutes)

    def test_admin_can_update_maintenance_records(self):
        client = self._client()
        headers = self._admin_headers(client)
        seeded = self._seed_admin_route(client, headers)

        attraction = client.put(
            f"/api/recommendation/admin/attractions/{seeded['attraction_id']}",
            json={'name': '古城墙修订', 'category': '历史遗迹', 'tags': ['history']},
            headers=headers,
        )
        template = client.put(
            f"/api/recommendation/admin/templates/{seeded['template_id']}",
            json={'name': '历史文化修订线', 'interest_tags': ['history'], 'duration_minutes': 150},
            headers=headers,
        )
        stop = client.post(
            f"/api/recommendation/admin/templates/{seeded['template_id']}/stops",
            json={'id': seeded['stop_id'], 'attraction_id': seeded['attraction_id'], 'order_index': 1, 'stay_minutes': 45},
            headers=headers,
        )
        material = client.post(
            '/api/recommendation/admin/materials',
            json={'id': seeded['material_id'], 'attraction_id': seeded['attraction_id'], 'interest_tag': 'history', 'script': '更新讲解。'},
            headers=headers,
        )

        stops = client.get(f"/api/recommendation/admin/templates/{seeded['template_id']}/stops", headers=headers)
        materials = client.get('/api/recommendation/admin/materials', headers=headers)

        self.assertEqual(200, attraction.status_code, attraction.get_data(as_text=True))
        self.assertEqual(200, template.status_code, template.get_data(as_text=True))
        self.assertEqual(200, stop.status_code, stop.get_data(as_text=True))
        self.assertEqual(200, material.status_code, material.get_data(as_text=True))
        self.assertEqual(45, stops.get_json()['items'][0]['stay_minutes'])
        self.assertEqual('更新讲解。', materials.get_json()['items'][0]['script'])

    def test_admin_can_initialize_attraction_drafts_from_tourism_visits(self):
        client = self._client()
        headers = self._admin_headers(client)
        self._write_tourism_visit()

        initialized = client.post('/api/recommendation/admin/initialize-attractions', json={'limit': 10}, headers=headers)

        self.assertEqual(200, initialized.status_code, initialized.get_data(as_text=True))
        self.assertEqual(1, initialized.get_json()['created'])

    def test_admin_can_import_and_export_recommendation_data(self):
        client = self._client()
        headers = self._admin_headers(client)
        self._seed_admin_route(client, headers)

        exported = client.get('/api/recommendation/admin/export', headers=headers)
        dry_run = client.post(
            '/api/recommendation/admin/import',
            json={'dry_run': True, 'attractions': [{'name': '花谷', 'category': '自然风光', 'tags': ['nature']}]},
            headers=headers,
        )
        imported = client.post(
            '/api/recommendation/admin/import',
            json={'attractions': [{'name': '花谷', 'category': '自然风光', 'tags': ['nature']}]},
            headers=headers,
        )
        csv_export = client.get('/api/recommendation/admin/attractions/export?format=csv', headers=headers)

        self.assertEqual(200, exported.status_code, exported.get_data(as_text=True))
        self.assertIn('attractions', exported.get_json())
        self.assertEqual(200, dry_run.status_code, dry_run.get_data(as_text=True))
        self.assertTrue(dry_run.get_json()['dry_run'])
        self.assertEqual(200, imported.status_code, imported.get_data(as_text=True))
        self.assertEqual(1, imported.get_json()['created']['attractions'])
        self.assertEqual(200, csv_export.status_code, csv_export.get_data(as_text=True))
        self.assertIn('text/csv', csv_export.content_type)
        self.assertIn('古城墙', csv_export.get_data(as_text=True))

        csv_file = io.BytesIO('name,category,tags\n森林步道,自然风光,nature|walk\n'.encode('utf-8-sig'))
        csv_import = client.post(
            '/api/recommendation/admin/attractions/import',
            data={'file': (csv_file, 'attractions.csv')},
            content_type='multipart/form-data',
            headers=headers,
        )

        self.assertEqual(200, csv_import.status_code, csv_import.get_data(as_text=True))
        self.assertEqual(1, csv_import.get_json()['created'])

    def _seed_admin_route(self, client, headers):
        attraction = client.post(
            '/api/recommendation/admin/attractions',
            json={'name': '古城墙', 'category': '历史遗迹', 'tags': ['history'], 'satisfaction': 4.8, 'popularity': 90},
            headers=headers,
        )
        self.assertEqual(200, attraction.status_code, attraction.get_data(as_text=True))
        template = client.post(
            '/api/recommendation/admin/templates',
            json={'name': '历史文化半日线', 'interest_tags': ['history'], 'duration_minutes': 120},
            headers=headers,
        )
        self.assertEqual(200, template.status_code, template.get_data(as_text=True))
        stop = client.post(
            f"/api/recommendation/admin/templates/{template.get_json()['id']}/stops",
            json={'attraction_id': attraction.get_json()['id'], 'order_index': 1, 'stay_minutes': 35},
            headers=headers,
        )
        material = client.post(
            '/api/recommendation/admin/materials',
            json={'attraction_id': attraction.get_json()['id'], 'interest_tag': 'history', 'title': '城墙讲解', 'script': '讲述建城背景。'},
            headers=headers,
        )
        return {
            'attraction_id': attraction.get_json()['id'],
            'template_id': template.get_json()['id'],
            'stop_id': stop.get_json()['id'],
            'material_id': material.get_json()['id'],
        }

    def _exercise_edge_routes(self, client, headers, attraction_id):
        edge = client.post(
            '/api/recommendation/admin/edges',
            json={'from_attraction_id': attraction_id, 'to_attraction_id': attraction_id, 'walk_minutes': 6},
            headers=headers,
        )
        edges = client.get('/api/recommendation/admin/edges', headers=headers)
        deleted_edge = client.delete(f"/api/recommendation/admin/edges/{edge.get_json()['id']}", headers=headers)

        self.assertEqual(200, edge.status_code, edge.get_data(as_text=True))
        self.assertEqual(200, edges.status_code, edges.get_data(as_text=True))
        self.assertEqual(200, deleted_edge.status_code, deleted_edge.get_data(as_text=True))
        return edges.get_json()['items'][0]['walk_minutes']

    def _write_tourism_visit(self):
        conn = sqlite3.connect(os.path.join('memory', 'tourism.db'))
        conn.execute(
            '''CREATE TABLE tourism_visit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attraction_name TEXT, attraction_type TEXT, satisfaction INTEGER
            )'''
        )
        conn.execute(
            '''INSERT INTO tourism_visit (attraction_name, attraction_type, satisfaction)
            VALUES ('湖畔栈道', '自然风光', 5)'''
        )
        conn.commit()
        conn.close()

    def _set_global_auth(self, enabled):
        with open('config.json', 'r', encoding='utf-8') as file:
            config = json.load(file)
        config['auth']['enabled'] = enabled
        with open('config.json', 'w', encoding='utf-8') as file:
            json.dump(config, file)


if __name__ == '__main__':
    unittest.main(verbosity=2)
