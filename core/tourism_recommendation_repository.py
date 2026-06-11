from core.tourism_recommendation_schema import connect
from core.tourism_recommendation_utils import now_seconds, row_to_dict


class RecommendationRepository:
    def _upsert(self, table, payload, fields):
        item_id = payload.get('id')
        data = {key: payload.get(key) for key in fields if key in payload}
        data['updated_at'] = now_seconds()
        if data.get('created_at') is None:
            data['created_at'] = now_seconds()
        if item_id:
            return self._update(table, item_id, data)
        return self._insert(table, data, tuple(data.keys()))

    def _insert(self, table, payload, fields):
        with self.lock:
            conn = connect(self.db_path)
            try:
                names = ', '.join(fields)
                marks = ', '.join('?' for _ in fields)
                values = [payload.get(key) for key in fields]
                cursor = conn.execute(f'INSERT INTO {table} ({names}) VALUES ({marks})', values)
                conn.commit()
                return cursor.lastrowid
            finally:
                conn.close()

    def _update(self, table, item_id, payload):
        with self.lock:
            conn = connect(self.db_path)
            try:
                clause = ', '.join(f'{key} = ?' for key in payload)
                conn.execute(f'UPDATE {table} SET {clause} WHERE id = ?', [*payload.values(), item_id])
                conn.commit()
                return int(item_id)
            finally:
                conn.close()

    def _get(self, table, item_id):
        rows = self._query(f'SELECT * FROM {table} WHERE id = ? AND deleted_at IS NULL', [item_id])
        return rows[0] if rows else None

    def _list(self, table, include_deleted=False):
        where = '' if include_deleted else ' WHERE deleted_at IS NULL'
        return self._query(f'SELECT * FROM {table}{where} ORDER BY id')

    def _query(self, sql, params=None):
        conn = connect(self.db_path)
        try:
            rows = conn.execute(sql, params or []).fetchall()
            return [row_to_dict(row) for row in rows]
        finally:
            conn.close()

    def _update_flag(self, table, item_id, column, value):
        with self.lock:
            conn = connect(self.db_path)
            try:
                conn.execute(
                    f'UPDATE {table} SET {column} = ?, updated_at = ? WHERE id = ?',
                    (value, now_seconds(), item_id),
                )
                conn.commit()
            finally:
                conn.close()

    def _soft_delete(self, table, item_id):
        with self.lock:
            conn = connect(self.db_path)
            try:
                conn.execute(
                    f'UPDATE {table} SET deleted_at = ?, updated_at = ? WHERE id = ?',
                    (now_seconds(), now_seconds(), item_id),
                )
                conn.commit()
            finally:
                conn.close()
