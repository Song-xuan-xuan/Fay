from core.tourism_recommendation_algorithm import DEFAULT_CONFIG
from core.tourism_recommendation_schema import connect
from core.tourism_recommendation_utils import bool_int, json_dumps, json_loads, now_seconds, row_to_dict, tags_from_value


class RecommendationCatalogMixin:
    def upsert_attraction(self, data):
        payload = dict(data or {})
        payload['tags_json'] = json_dumps(tags_from_value(payload.pop('tags', [])))
        payload['indoor'] = bool_int(payload.get('indoor'))
        payload['enabled'] = 1 if payload.get('enabled', True) else 0
        fields = (
            'name', 'category', 'summary', 'tags_json', 'visit_minutes', 'difficulty',
            'indoor', 'accessibility', 'budget_level', 'popularity', 'satisfaction', 'enabled',
        )
        return self._upsert('recommendation_attraction', payload, fields)

    def get_attraction(self, attraction_id):
        row = self._get('recommendation_attraction', attraction_id)
        return self._decode_attraction(row) if row else None

    def list_attractions(self, include_deleted=False):
        rows = self._list('recommendation_attraction', include_deleted=include_deleted)
        return [self._decode_attraction(row) for row in rows]

    def set_attraction_enabled(self, attraction_id, enabled):
        self._update_flag('recommendation_attraction', attraction_id, 'enabled', bool_int(enabled))

    def delete_attraction(self, attraction_id):
        self._soft_delete('recommendation_attraction', attraction_id)

    def upsert_route_template(self, data):
        payload = dict(data or {})
        payload['interest_tags_json'] = json_dumps(tags_from_value(payload.pop('interest_tags', [])))
        payload['enabled'] = 1 if payload.get('enabled', True) else 0
        fields = (
            'name', 'summary', 'interest_tags_json', 'duration_minutes', 'intensity',
            'budget_level', 'start_attraction_id', 'end_attraction_id', 'enabled',
        )
        return self._upsert('recommendation_route_template', payload, fields)

    def get_route_template(self, template_id):
        row = self._get('recommendation_route_template', template_id)
        return self._decode_template(row) if row else None

    def list_route_templates(self, include_deleted=False):
        rows = self._list('recommendation_route_template', include_deleted=include_deleted)
        return [self._decode_template(row) for row in rows]

    def delete_route_template(self, template_id):
        self._soft_delete('recommendation_route_template', template_id)

    def upsert_route_stop(self, template_id, attraction_id, order_index=0, stay_minutes=30, **options):
        payload = {
            'id': options.get('id'), 'template_id': template_id, 'attraction_id': attraction_id,
            'order_index': order_index, 'stay_minutes': stay_minutes,
            'note': options.get('note', ''), 'enabled': bool_int(options.get('enabled', True)),
        }
        fields = ('template_id', 'attraction_id', 'order_index', 'stay_minutes', 'note', 'enabled')
        return self._upsert('recommendation_route_stop', payload, fields)

    def list_route_stops(self, template_id=None):
        sql = 'SELECT * FROM recommendation_route_stop WHERE deleted_at IS NULL'
        params = []
        if template_id is not None:
            sql += ' AND template_id = ?'
            params.append(template_id)
        return self._query(sql + ' ORDER BY template_id, order_index, id', params)

    def delete_route_stop(self, stop_id):
        self._soft_delete('recommendation_route_stop', stop_id)

    def upsert_route_edge(self, from_attraction_id, to_attraction_id, **data):
        payload = {
            'id': data.get('id'), 'from_attraction_id': from_attraction_id,
            'to_attraction_id': to_attraction_id, 'walk_minutes': data.get('walk_minutes', 0),
            'distance_meters': data.get('distance_meters', 0), 'difficulty': data.get('difficulty', 1),
            'accessibility': data.get('accessibility', ''), 'bidirectional': bool_int(data.get('bidirectional', True)),
            'notes': data.get('notes', ''), 'enabled': bool_int(data.get('enabled', True)),
        }
        fields = (
            'from_attraction_id', 'to_attraction_id', 'walk_minutes', 'distance_meters',
            'difficulty', 'accessibility', 'bidirectional', 'notes', 'enabled',
        )
        return self._upsert('recommendation_route_edge', payload, fields)

    def list_route_edges(self):
        return self._query('SELECT * FROM recommendation_route_edge WHERE deleted_at IS NULL ORDER BY id')

    def delete_route_edge(self, edge_id):
        self._soft_delete('recommendation_route_edge', edge_id)

    def upsert_explanation_material(self, attraction_id, interest_tag='', title='', script='', **data):
        payload = {
            'id': data.get('id'), 'attraction_id': attraction_id, 'interest_tag': interest_tag,
            'title': title, 'focus': data.get('focus', title), 'script': script,
            'enabled': bool_int(data.get('enabled', True)),
        }
        fields = ('attraction_id', 'interest_tag', 'title', 'focus', 'script', 'enabled')
        return self._upsert('recommendation_explanation_material', payload, fields)

    def list_explanation_materials(self, attraction_id=None):
        sql = 'SELECT * FROM recommendation_explanation_material WHERE deleted_at IS NULL'
        params = []
        if attraction_id is not None:
            sql += ' AND attraction_id = ?'
            params.append(attraction_id)
        return self._query(sql + ' ORDER BY attraction_id, id', params)

    def delete_explanation_material(self, material_id):
        self._soft_delete('recommendation_explanation_material', material_id)

    def get_config(self):
        rows = self._query('SELECT key, value_json FROM recommendation_config ORDER BY key')
        config = {row['key']: json_loads(row['value_json'], {}) for row in rows}
        weights = {**DEFAULT_CONFIG['weights'], **config.get('weights', {})}
        return {**DEFAULT_CONFIG, **config, 'weights': weights}

    def update_config(self, values):
        with self.lock:
            conn = connect(self.db_path)
            try:
                for key, value in (values or {}).items():
                    conn.execute(
                        '''INSERT INTO recommendation_config (key, value_json, updated_at)
                        VALUES (?, ?, ?)
                        ON CONFLICT(key) DO UPDATE SET value_json = excluded.value_json,
                        updated_at = excluded.updated_at''',
                        (key, json_dumps(value), now_seconds()),
                    )
                conn.commit()
            finally:
                conn.close()
        return self.get_config()

    def _decode_attraction(self, row):
        item = row_to_dict(row)
        item['tags'] = json_loads(item.pop('tags_json'), [])
        item['enabled'] = bool(item.get('enabled'))
        item['indoor'] = bool(item.get('indoor'))
        return item

    def _decode_template(self, row):
        item = row_to_dict(row)
        item['interest_tags'] = json_loads(item.pop('interest_tags_json'), [])
        item['enabled'] = bool(item.get('enabled'))
        return item
