class RecommendationImportDedupeMixin:
    def _with_existing_id(self, item, table, **conditions):
        payload = dict(item or {})
        if payload.get('id'):
            return payload
        item_id = self._find_active_id(table, conditions)
        if item_id:
            payload['id'] = item_id
        return payload

    def _existing_route_stop_id(self, template_id, order_index):
        return self._find_active_id(
            'recommendation_route_stop',
            {'template_id': template_id, 'order_index': order_index},
        )

    def _existing_material_id(self, attraction_id, interest_tag, title):
        return self._find_active_id('recommendation_explanation_material', {
            'attraction_id': attraction_id,
            'interest_tag': interest_tag,
            'title': title,
        })

    def _existing_edge_id(self, from_id, to_id):
        return self._find_active_id('recommendation_route_edge', {
            'from_attraction_id': from_id,
            'to_attraction_id': to_id,
        })

    def _find_active_id(self, table, conditions):
        rows = self._active_rows(table, conditions, limit=1)
        return rows[0]['id'] if rows else None

    def _active_rows(self, table, conditions, limit=None):
        if not conditions:
            return []
        clause = ' AND '.join(f'{key} = ?' for key in conditions)
        sql = f'SELECT id FROM {table} WHERE {clause} AND deleted_at IS NULL ORDER BY id'
        if limit:
            sql += f' LIMIT {int(limit)}'
        return self._query(sql, list(conditions.values()))

    def _dedupe_imported_data(self, data, attraction_map, template_map):
        self._dedupe_imported_templates(data.get('templates') or [])
        self._dedupe_imported_attractions(data.get('attractions') or [])
        self._dedupe_imported_stops(data.get('stops') or [], template_map)
        self._dedupe_imported_materials(data.get('materials') or [], attraction_map)
        self._dedupe_imported_edges(data.get('edges') or [], attraction_map)

    def _dedupe_imported_attractions(self, items):
        for item in items:
            name = item.get('name')
            if name and not self._skip_import_item(item):
                self._dedupe_rows(
                    'recommendation_attraction',
                    {'name': name},
                    self._delete_attraction_dependencies,
                )

    def _dedupe_imported_templates(self, items):
        for item in items:
            name = item.get('name')
            if name and not self._skip_import_item(item):
                self._dedupe_rows(
                    'recommendation_route_template',
                    {'name': name},
                    self._delete_template_dependencies,
                )

    def _dedupe_imported_stops(self, items, template_map):
        for item in items:
            template_id = self._resolve_reference(
                item, template_map, 'template_external_id', 'template_id', 'template_name',
            )
            if template_id:
                order_index = item.get('order_index', 0) or 0
                self._dedupe_rows('recommendation_route_stop', {
                    'template_id': template_id,
                    'order_index': order_index,
                })

    def _dedupe_imported_materials(self, items, attraction_map):
        for item in items:
            attraction_id = self._resolve_reference(
                item, attraction_map, 'attraction_external_id', 'attraction_id', 'attraction_name',
            )
            if attraction_id and not self._skip_import_item(item):
                self._dedupe_rows('recommendation_explanation_material', {
                    'attraction_id': attraction_id,
                    'interest_tag': item.get('interest_tag', ''),
                    'title': item.get('title', ''),
                })

    def _dedupe_imported_edges(self, items, attraction_map):
        for item in items:
            from_id = self._resolve_reference(
                item, attraction_map, 'from_attraction_external_id', 'from_attraction_id',
            )
            to_id = self._resolve_reference(
                item, attraction_map, 'to_attraction_external_id', 'to_attraction_id',
            )
            if from_id and to_id and not self._skip_import_item(item):
                self._dedupe_rows('recommendation_route_edge', {
                    'from_attraction_id': from_id,
                    'to_attraction_id': to_id,
                })

    def _dedupe_rows(self, table, conditions, on_delete=None):
        rows = self._active_rows(table, conditions)
        for row in rows[1:]:
            if on_delete:
                on_delete(row['id'])
            self._soft_delete(table, row['id'])

    def _delete_template_dependencies(self, template_id):
        self._soft_delete_where('recommendation_route_stop', {'template_id': template_id})

    def _delete_attraction_dependencies(self, attraction_id):
        self._soft_delete_where('recommendation_route_stop', {'attraction_id': attraction_id})
        self._soft_delete_where('recommendation_explanation_material', {'attraction_id': attraction_id})
        self._soft_delete_where('recommendation_route_edge', {'from_attraction_id': attraction_id})
        self._soft_delete_where('recommendation_route_edge', {'to_attraction_id': attraction_id})

    def _soft_delete_where(self, table, conditions):
        for row in self._active_rows(table, conditions):
            self._soft_delete(table, row['id'])
