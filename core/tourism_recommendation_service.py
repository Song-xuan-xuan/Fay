import os
import threading
from collections import defaultdict

from core.tourism_recommendation_algorithm import build_recommendation
from core.tourism_recommendation_catalog import RecommendationCatalogMixin
from core.tourism_recommendation_import import RecommendationImportExportMixin
from core.tourism_recommendation_repository import RecommendationRepository
from core.tourism_recommendation_schema import ensure_schema, list_tables
from core.tourism_recommendation_utils import DEFAULT_DB_PATH, json_dumps, json_loads, now_seconds


class TourismRecommendationService(
    RecommendationImportExportMixin,
    RecommendationCatalogMixin,
    RecommendationRepository,
):
    def __init__(self, db_path=DEFAULT_DB_PATH, tourism_db_path=None):
        self.db_path = db_path
        self.tourism_db_path = tourism_db_path or os.path.join('memory', 'tourism.db')
        self.lock = threading.RLock()
        ensure_schema(self.db_path)

    def list_tables(self):
        return list_tables(self.db_path)

    def save_user_preferences(self, user_id, preferences):
        payload = {'user_id': int(user_id), **(preferences or {})}
        sql = '''INSERT INTO recommendation_user_preference (user_id, preference_json, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET preference_json = excluded.preference_json,
        updated_at = excluded.updated_at'''
        self._execute(sql, (int(user_id), json_dumps(payload), now_seconds()))
        return payload

    def get_user_preferences(self, user_id):
        rows = self._query(
            'SELECT preference_json FROM recommendation_user_preference WHERE user_id = ?',
            [int(user_id)],
        )
        return json_loads(rows[0]['preference_json'], {}) if rows else None

    def delete_user_preferences(self, user_id):
        self._execute('DELETE FROM recommendation_user_preference WHERE user_id = ?', (int(user_id),))

    def recommend(self, request_data):
        payload = self._merge_preferences(dict(request_data or {}))
        result = build_recommendation(payload, *self._dataset(), config=self.get_config())
        log_id = self._record_recommendation(payload, result)
        result['recommendation_id'] = log_id
        if result.get('main_route'):
            result['main_route']['recommendation_id'] = log_id
        return result

    def get_recommendation(self, recommendation_id, user_id=None):
        sql = 'SELECT * FROM recommendation_log WHERE id = ?'
        params = [recommendation_id]
        if user_id is not None:
            sql += ' AND user_id = ?'
            params.append(user_id)
        rows = self._query(sql, params)
        return self._decode_log(rows[0]) if rows else None

    def list_recommendations(self, user_id=None, limit=20):
        sql = 'SELECT * FROM recommendation_log'
        params = []
        if user_id is not None:
            sql += ' WHERE user_id = ?'
            params.append(user_id)
        sql += ' ORDER BY id DESC LIMIT ?'
        params.append(int(limit))
        return [self._decode_log(row) for row in self._query(sql, params)]

    def submit_feedback(self, recommendation_id, user_id, action='', rating=None, comment=''):
        payload = {
            'recommendation_id': recommendation_id,
            'user_id': user_id,
            'action': action,
            'rating': rating,
            'comment': comment,
            'created_at': now_seconds(),
        }
        payload['id'] = self._insert('recommendation_feedback', payload, tuple(payload.keys()))
        return payload

    def _execute(self, sql, params):
        from core.tourism_recommendation_schema import connect

        with self.lock:
            conn = connect(self.db_path)
            try:
                conn.execute(sql, params)
                conn.commit()
            finally:
                conn.close()

    def _dataset(self):
        attractions = {item['id']: item for item in self.list_attractions()}
        templates = self.list_route_templates()
        stops = defaultdict(list)
        for stop in self.list_route_stops():
            if stop.get('enabled'):
                stops[stop['template_id']].append(stop)
        materials = defaultdict(list)
        for material in self.list_explanation_materials():
            materials[material['attraction_id']].append(material)
        return templates, stops, attractions, self._edge_map(), materials

    def _edge_map(self):
        edges = {}
        for row in self.list_route_edges():
            if row.get('enabled'):
                row['bidirectional'] = bool(row.get('bidirectional'))
                edges[(row['from_attraction_id'], row['to_attraction_id'])] = row
        return edges

    def _merge_preferences(self, payload):
        user_id = payload.get('user_id')
        preferences = self.get_user_preferences(user_id) if user_id is not None else None
        for key, value in (preferences or {}).items():
            payload.setdefault(key, value)
        return payload

    def _record_recommendation(self, request_data, result):
        breakdown = (result.get('main_route') or {}).get('score_breakdown') or {}
        return self._insert('recommendation_log', {
            'user_id': request_data.get('user_id'),
            'request_json': json_dumps(request_data),
            'result_json': json_dumps(result),
            'score_breakdown_json': json_dumps(breakdown),
            'created_at': now_seconds(),
        }, ('user_id', 'request_json', 'result_json', 'score_breakdown_json', 'created_at'))

    def _decode_log(self, row):
        item = dict(row)
        item['request'] = json_loads(item.pop('request_json'), {})
        item['result'] = json_loads(item.pop('result_json'), {})
        item['score_breakdown'] = json_loads(item.pop('score_breakdown_json'), {})
        return item
