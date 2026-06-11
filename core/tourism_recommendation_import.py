import os
import sqlite3

from core.tourism_recommendation_utils import now_seconds, row_to_dict, tags_from_value


class RecommendationImportExportMixin:
    def export_data(self):
        return {
            'attractions': self.list_attractions(),
            'templates': self.list_route_templates(),
            'stops': self.list_route_stops(),
            'edges': self.list_route_edges(),
            'materials': self.list_explanation_materials(),
            'config': self.get_config(),
            'exported_at': now_seconds(),
        }

    def import_data(self, payload, dry_run=False):
        data = payload or {}
        errors = self._validate_import_data(data)
        if errors or dry_run:
            return {'success': not errors, 'dry_run': bool(dry_run), 'errors': errors, 'created': self._empty_created()}
        created = self._empty_created()
        for item in data.get('attractions') or []:
            self.upsert_attraction(item)
            created['attractions'] += 1
        for item in data.get('templates') or []:
            self.upsert_route_template(item)
            created['templates'] += 1
        return {'success': True, 'dry_run': False, 'errors': [], 'created': created}

    def import_attractions(self, rows, dry_run=False):
        normalized = [self._normalize_attraction_row(row) for row in rows]
        errors = [f'第 {index + 1} 行缺少 name' for index, row in enumerate(normalized) if not row.get('name')]
        if errors or dry_run:
            return {'success': not errors, 'dry_run': bool(dry_run), 'errors': errors, 'created': 0}
        for row in normalized:
            self.upsert_attraction(row)
        return {'success': True, 'dry_run': False, 'errors': [], 'created': len(normalized)}

    def initialize_attractions_from_tourism(self, limit=100):
        if not os.path.exists(self.tourism_db_path):
            return {'success': False, 'row_count': 0, 'message': '旅游看板数据库不存在'}
        rows = self._tourism_rows(limit)
        created = 0
        for row in rows:
            if self._attraction_exists(row['attraction_name']):
                continue
            self.upsert_attraction({
                'name': row['attraction_name'], 'category': row['attraction_type'],
                'tags': [row['attraction_type']], 'popularity': row['visits'],
                'satisfaction': row['avg_satisfaction'], 'enabled': False,
            })
            created += 1
        return {'success': True, 'row_count': len(rows), 'created': created}

    def _validate_import_data(self, data):
        errors = []
        for index, item in enumerate(data.get('attractions') or []):
            if not str(item.get('name') or '').strip():
                errors.append(f'attractions[{index}].name 不能为空')
        for index, item in enumerate(data.get('templates') or []):
            if not str(item.get('name') or '').strip():
                errors.append(f'templates[{index}].name 不能为空')
        return errors

    def _empty_created(self):
        return {'attractions': 0, 'templates': 0, 'stops': 0, 'edges': 0, 'materials': 0}

    def _normalize_attraction_row(self, row):
        item = dict(row or {})
        tags = item.get('tags') or item.get('tags_json') or []
        if isinstance(tags, str):
            tags = tags.replace('|', ',').split(',')
        return {
            'name': str(item.get('name') or '').strip(),
            'category': item.get('category') or '',
            'summary': item.get('summary') or '',
            'tags': tags_from_value(tags),
            'visit_minutes': item.get('visit_minutes') or 30,
            'difficulty': item.get('difficulty') or 1,
            'indoor': item.get('indoor') or False,
            'enabled': item.get('enabled', True),
            'popularity': item.get('popularity') or 0,
            'satisfaction': item.get('satisfaction') or 0,
        }

    def _attraction_exists(self, name):
        rows = self._query('SELECT id FROM recommendation_attraction WHERE name = ? AND deleted_at IS NULL', [name])
        return bool(rows)

    def _tourism_rows(self, limit):
        conn = sqlite3.connect(self.tourism_db_path)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                '''SELECT attraction_name, attraction_type, COUNT(*) AS visits,
                AVG(satisfaction) AS avg_satisfaction FROM tourism_visit
                GROUP BY attraction_name, attraction_type ORDER BY visits DESC LIMIT ?''',
                (int(limit),),
            ).fetchall()
            return [row_to_dict(row) for row in rows]
        finally:
            conn.close()
