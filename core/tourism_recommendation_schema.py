import os
import sqlite3


SCHEMA_STATEMENTS = (
    '''CREATE TABLE IF NOT EXISTS recommendation_attraction (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT DEFAULT '',
        summary TEXT DEFAULT '',
        tags_json TEXT DEFAULT '[]',
        visit_minutes INTEGER DEFAULT 30,
        difficulty INTEGER DEFAULT 1,
        indoor INTEGER DEFAULT 0,
        accessibility TEXT DEFAULT '',
        budget_level TEXT DEFAULT '',
        popularity REAL DEFAULT 0,
        satisfaction REAL DEFAULT 0,
        enabled INTEGER DEFAULT 1,
        deleted_at INTEGER,
        created_at INTEGER,
        updated_at INTEGER
    )''',
    '''CREATE TABLE IF NOT EXISTS recommendation_route_template (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        summary TEXT DEFAULT '',
        interest_tags_json TEXT DEFAULT '[]',
        duration_minutes INTEGER DEFAULT 120,
        intensity TEXT DEFAULT 'medium',
        budget_level TEXT DEFAULT '',
        start_attraction_id INTEGER,
        end_attraction_id INTEGER,
        enabled INTEGER DEFAULT 1,
        deleted_at INTEGER,
        created_at INTEGER,
        updated_at INTEGER
    )''',
    '''CREATE TABLE IF NOT EXISTS recommendation_route_stop (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_id INTEGER NOT NULL,
        attraction_id INTEGER NOT NULL,
        order_index INTEGER DEFAULT 0,
        stay_minutes INTEGER DEFAULT 30,
        note TEXT DEFAULT '',
        enabled INTEGER DEFAULT 1,
        deleted_at INTEGER,
        created_at INTEGER,
        updated_at INTEGER
    )''',
    '''CREATE TABLE IF NOT EXISTS recommendation_route_edge (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_attraction_id INTEGER NOT NULL,
        to_attraction_id INTEGER NOT NULL,
        walk_minutes INTEGER DEFAULT 0,
        distance_meters INTEGER DEFAULT 0,
        difficulty INTEGER DEFAULT 1,
        accessibility TEXT DEFAULT '',
        bidirectional INTEGER DEFAULT 1,
        notes TEXT DEFAULT '',
        enabled INTEGER DEFAULT 1,
        deleted_at INTEGER,
        created_at INTEGER,
        updated_at INTEGER
    )''',
    '''CREATE TABLE IF NOT EXISTS recommendation_explanation_material (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        attraction_id INTEGER NOT NULL,
        interest_tag TEXT DEFAULT '',
        title TEXT DEFAULT '',
        focus TEXT DEFAULT '',
        script TEXT DEFAULT '',
        enabled INTEGER DEFAULT 1,
        deleted_at INTEGER,
        created_at INTEGER,
        updated_at INTEGER
    )''',
    '''CREATE TABLE IF NOT EXISTS recommendation_config (
        key TEXT PRIMARY KEY,
        value_json TEXT NOT NULL,
        updated_at INTEGER
    )''',
    '''CREATE TABLE IF NOT EXISTS recommendation_user_preference (
        user_id INTEGER PRIMARY KEY,
        preference_json TEXT NOT NULL,
        updated_at INTEGER
    )''',
    '''CREATE TABLE IF NOT EXISTS recommendation_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        request_json TEXT NOT NULL,
        result_json TEXT NOT NULL,
        score_breakdown_json TEXT NOT NULL,
        created_at INTEGER
    )''',
    '''CREATE TABLE IF NOT EXISTS recommendation_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        recommendation_id INTEGER,
        user_id INTEGER,
        action TEXT DEFAULT '',
        rating INTEGER,
        comment TEXT DEFAULT '',
        created_at INTEGER
    )''',
    '''CREATE TABLE IF NOT EXISTS recommendation_import_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source TEXT DEFAULT '',
        row_count INTEGER DEFAULT 0,
        status TEXT DEFAULT '',
        error TEXT DEFAULT '',
        dry_run INTEGER DEFAULT 0,
        created_at INTEGER
    )''',
    'CREATE INDEX IF NOT EXISTS idx_recommendation_attraction_enabled ON recommendation_attraction(enabled, deleted_at)',
    'CREATE INDEX IF NOT EXISTS idx_recommendation_stop_template ON recommendation_route_stop(template_id, order_index)',
    'CREATE INDEX IF NOT EXISTS idx_recommendation_log_user ON recommendation_log(user_id, created_at)',
)


def connect(db_path):
    folder = os.path.dirname(db_path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema(db_path):
    conn = connect(db_path)
    try:
        for statement in SCHEMA_STATEMENTS:
            conn.execute(statement)
        conn.commit()
    finally:
        conn.close()


def list_tables(db_path):
    ensure_schema(db_path)
    conn = connect(db_path)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
        ).fetchall()
        return [row['name'] for row in rows]
    finally:
        conn.close()
