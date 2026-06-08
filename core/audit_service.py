import functools
import json
import os
import sqlite3
import threading
import time


DB_PATH = os.path.join('memory', 'user_profiles.db')


def synchronized(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        with self.lock:
            return func(self, *args, **kwargs)
    return wrapper


__audit_service = None


def new_instance():
    global __audit_service
    if __audit_service is None:
        __audit_service = AuditService()
        __audit_service.init_db()
    return __audit_service


class AuditService:
    def __init__(self):
        self.lock = threading.RLock()

    def _connect(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        return sqlite3.connect(DB_PATH)

    def init_db(self):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS T_AuditLog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            resource TEXT,
            details TEXT,
            ip_address TEXT,
            timestamp INTEGER NOT NULL
        )''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_user ON T_AuditLog(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_action ON T_AuditLog(action)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON T_AuditLog(timestamp)')
        conn.commit()
        conn.close()

    @synchronized
    def log(self, user_id, username, action, resource='', details=None, ip_address=''):
        self.init_db()
        details_text = json.dumps(details or {}, ensure_ascii=False)
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO T_AuditLog (user_id, username, action, resource, details, ip_address, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (int(user_id or 0), username or '', action, resource or '', details_text, ip_address or '', int(time.time())),
        )
        log_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return log_id

    def _row_to_log(self, row):
        details = {}
        if row[5]:
            try:
                details = json.loads(row[5])
            except json.JSONDecodeError:
                details = {'raw': row[5]}
        return {
            'id': row[0],
            'user_id': row[1],
            'username': row[2],
            'action': row[3],
            'resource': row[4],
            'details': details,
            'ip_address': row[6],
            'timestamp': row[7],
        }

    @synchronized
    def list_logs(self, username=None, action=None, limit=50, offset=0):
        self.init_db()
        where = []
        params = []
        if username:
            where.append('username = ?')
            params.append(username)
        if action:
            where.append('action = ?')
            params.append(action)
        where_sql = (' WHERE ' + ' AND '.join(where)) if where else ''
        limit = max(1, min(int(limit or 50), 500))
        offset = max(0, int(offset or 0))

        conn = self._connect()
        total = conn.execute(f'SELECT COUNT(*) FROM T_AuditLog{where_sql}', params).fetchone()[0]
        rows = conn.execute(
            f'''SELECT id, user_id, username, action, resource, details, ip_address, timestamp
            FROM T_AuditLog{where_sql} ORDER BY id DESC LIMIT ? OFFSET ?''',
            (*params, limit, offset),
        ).fetchall()
        conn.close()
        return {'list': [self._row_to_log(row) for row in rows], 'total': total}

    @synchronized
    def cleanup_older_than(self, days=90):
        cutoff = int(time.time()) - int(days) * 86400
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM T_AuditLog WHERE timestamp < ?', (cutoff,))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted
