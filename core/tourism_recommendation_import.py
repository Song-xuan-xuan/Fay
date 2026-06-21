import os
import sqlite3

from core.tourism_recommendation_import_dedupe import RecommendationImportDedupeMixin
from core.tourism_recommendation_utils import now_seconds, row_to_dict, tags_from_value


class RecommendationImportExportMixin(RecommendationImportDedupeMixin):
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
        attraction_map, created['attractions'] = self._import_attractions(data.get('attractions') or [])
        template_map, created['templates'] = self._import_templates(data.get('templates') or [])
        created['stops'] = self._import_stops(data.get('stops') or [], attraction_map, template_map)
        created['materials'] = self._import_materials(data.get('materials') or [], attraction_map)
        created['edges'] = self._import_edges(data.get('edges') or [], attraction_map)
        if data.get('config'):
            self.update_config(data.get('config') or {})
            created['config'] = len(data.get('config') or {})
        self._dedupe_imported_data(data, attraction_map, template_map)
        return {'success': True, 'dry_run': False, 'errors': [], 'created': created}

    def import_attractions(self, rows, dry_run=False):
        normalized = [self._normalize_attraction_row(row) for row in rows]
        errors = [f'第 {index + 1} 行缺少 name' for index, row in enumerate(normalized) if not row.get('name')]
        if errors or dry_run:
            return {'success': not errors, 'dry_run': bool(dry_run), 'errors': errors, 'created': 0}
        for row in normalized:
            payload = self._with_existing_id(row, 'recommendation_attraction', name=row.get('name'))
            self.upsert_attraction(payload)
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
        return {'attractions': 0, 'templates': 0, 'stops': 0, 'edges': 0, 'materials': 0, 'config': 0}

    def _import_attractions(self, items):
        references = {}
        created = 0
        for item in items:
            if self._skip_import_item(item):
                continue
            payload = self._with_existing_id(item, 'recommendation_attraction', name=item.get('name'))
            item_id = self.upsert_attraction(payload)
            self._remember_reference(references, item, item_id, ('external_id', 'id', 'name'))
            created += 1
        return references, created

    def _import_templates(self, items):
        references = {}
        created = 0
        for item in items:
            if self._skip_import_item(item):
                continue
            payload = self._with_existing_id(item, 'recommendation_route_template', name=item.get('name'))
            item_id = self.upsert_route_template(payload)
            self._remember_reference(references, item, item_id, ('external_id', 'id', 'name'))
            created += 1
        return references, created

    def _import_stops(self, items, attraction_map, template_map):
        created = 0
        for item in items:
            template_id = self._resolve_reference(item, template_map, 'template_external_id', 'template_id', 'template_name')
            if not template_id:
                continue
            if self._skip_import_item(item):
                created += self._import_route_node(template_id, item)
                continue
            attraction_id = self._resolve_reference(
                item, attraction_map, 'attraction_external_id', 'attraction_id', 'attraction_name', 'raw_stop_name',
            )
            if template_id and attraction_id:
                node_type = 'draft' if not item.get('enabled', True) else 'attraction'
                order_index = item.get('order_index', 0) or 0
                item_id = item.get('id') or self._existing_route_stop_id(template_id, order_index)
                self.upsert_route_stop(
                    template_id, attraction_id, order_index, item.get('stay_minutes', 30),
                    id=item_id, note=item.get('note', ''), enabled=item.get('enabled', True),
                    node_name=self._route_node_name(item), node_type=item.get('node_type') or node_type,
                )
                created += 1
        return created

    def _import_route_node(self, template_id, item):
        node_name = self._route_node_name(item)
        if not node_name:
            return 0
        order_index = item.get('order_index', 0) or 0
        item_id = item.get('id') or self._existing_route_stop_id(template_id, order_index)
        self.upsert_route_stop(
            template_id, 0, order_index, item.get('stay_minutes', 0),
            id=item_id, note=item.get('note', ''), enabled=True,
            node_name=node_name, node_type=item.get('node_type') or self._route_node_type(node_name),
        )
        return 1

    def _import_materials(self, items, attraction_map):
        created = 0
        for item in items:
            if self._skip_import_item(item):
                continue
            attraction_id = self._resolve_reference(item, attraction_map, 'attraction_external_id', 'attraction_id', 'attraction_name')
            if attraction_id:
                item_id = item.get('id') or self._existing_material_id(
                    attraction_id, item.get('interest_tag', ''), item.get('title', ''),
                )
                self.upsert_explanation_material(
                    attraction_id, item.get('interest_tag', ''), item.get('title', ''),
                    item.get('script', ''), id=item_id, focus=item.get('focus', ''),
                    enabled=item.get('enabled', True),
                )
                created += 1
        return created

    def _import_edges(self, items, attraction_map):
        created = 0
        for item in items:
            if self._skip_import_item(item):
                continue
            from_id = self._resolve_reference(item, attraction_map, 'from_attraction_external_id', 'from_attraction_id')
            to_id = self._resolve_reference(item, attraction_map, 'to_attraction_external_id', 'to_attraction_id')
            if from_id and to_id:
                edge_data = {key: value for key, value in item.items() if key not in (
                    'from_attraction_external_id', 'to_attraction_external_id', 'from_attraction_id', 'to_attraction_id',
                )}
                edge_data['id'] = edge_data.get('id') or self._existing_edge_id(from_id, to_id)
                self.upsert_route_edge(from_id, to_id, **edge_data)
                created += 1
        return created

    def _skip_import_item(self, item):
        return str((item or {}).get('review_status') or '').strip() == '跳过'

    def _route_node_name(self, item):
        return str(
            item.get('node_name') or item.get('raw_stop_name') or item.get('attraction_name') or item.get('name') or ''
        ).strip()

    def _route_node_type(self, name):
        text = str(name or '')
        if any(marker in text for marker in ('入口', '入园', '进园')):
            return 'start'
        if any(marker in text for marker in ('出口', '出园', '离园')):
            return 'end'
        return 'path'

    def _remember_reference(self, references, item, item_id, keys):
        for key in keys:
            value = item.get(key)
            if value not in (None, ''):
                references[str(value)] = item_id

    def _resolve_reference(self, item, references, *keys):
        for key in keys:
            value = item.get(key)
            if value in (None, ''):
                continue
            mapped = references.get(str(value))
            if mapped:
                return mapped
            if key.endswith('_id') and str(value).isdigit():
                return int(value)
        return None

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
