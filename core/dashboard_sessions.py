import sqlite3


SESSION_TIMEOUT_MS = 30 * 60 * 1000


def derive_sessions(messages):
    sessions = []
    active = {}
    for message in messages:
        _msg_id, content, created_ms, username, uid, _topic = message[:6]
        if not content:
            continue
        key = uid or username or 'anonymous'
        previous = active.get(key)
        if previous is None or created_ms - previous['last_active_at'] > SESSION_TIMEOUT_MS:
            previous = {
                'key': key,
                'username': username,
                'started_at': created_ms,
                'last_active_at': created_ms,
                'message_count': 0,
            }
            sessions.append(previous)
        previous['last_active_at'] = created_ms
        previous['message_count'] += 1
        active[key] = previous
    return sessions


def load_service_sessions(db_path, start_ms=0):
    conn = sqlite3.connect(db_path)
    try:
        if not _table_exists(conn, 'T_ServiceSession'):
            return []
        columns = {row[1] for row in conn.execute('PRAGMA table_info(T_ServiceSession)').fetchall()}
        deleted_filter = 'AND deleted_at IS NULL' if 'deleted_at' in columns else ''
        rows = conn.execute(
            f'''SELECT id, user_id, username, started_at, last_active_at, message_count
            FROM T_ServiceSession
            WHERE COALESCE(message_count, 0) > 0
              AND (started_at >= ? OR last_active_at >= ?)
              {deleted_filter}
            ORDER BY started_at ASC, id ASC''',
            (int(start_ms or 0), int(start_ms or 0)),
        ).fetchall()
    finally:
        conn.close()
    return [_session_row(row) for row in rows]


def merge_persisted_and_legacy_sessions(db_path, messages, start_ms=0):
    persisted = load_service_sessions(db_path, start_ms)
    legacy_messages = [message for message in messages if _message_session_id(message) in (None, 0)]
    return persisted + derive_sessions(legacy_messages)


def _message_session_id(message):
    return message[6] if len(message) > 6 else None


def _session_row(row):
    session_id, user_id, username, started_at, last_active_at, message_count = row
    return {
        'id': session_id,
        'key': user_id or username or 'anonymous',
        'username': username,
        'started_at': int(started_at or 0),
        'last_active_at': int(last_active_at or started_at or 0),
        'message_count': int(message_count or 0),
    }


def _table_exists(conn, table):
    row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (table,)).fetchone()
    return row is not None
