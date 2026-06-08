import os
import sqlite3
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta


SESSION_TIMEOUT_MS = 30 * 60 * 1000
DAY_MS = 24 * 60 * 60 * 1000
LOW_SATISFACTION_MAX = 2

TOPIC_RULES = (
    ('交通路线', ('怎么去', '路线', '交通', '地铁', '公交', '停车', '导航')),
    ('门票开放', ('门票', '票价', '多少钱', '开放', '营业', '预约', '购票')),
    ('游览推荐', ('推荐', '攻略', '怎么玩', '路线安排', '一日游', '必玩')),
    ('餐饮购物', ('吃', '餐厅', '美食', '购物', '纪念品', '商店')),
    ('活动演出', ('活动', '演出', '表演', '节目', '烟花', '节庆')),
    ('服务设施', ('厕所', '寄存', '轮椅', '母婴', '设施', '客服', '投诉')),
    ('景点介绍', ('介绍', '历史', '文化', '景点', '有什么', '特色')),
)


def classify_question_topic(content):
    text = str(content or '').strip().lower()
    for topic, keywords in TOPIC_RULES:
        if any(keyword in text for keyword in keywords):
            return topic
    return '其他问题'


def mask_email(email):
    text = str(email or '').strip()
    if '@' not in text:
        return ''
    local, domain = text.split('@', 1)
    first = local[:1] or '*'
    return f'{first}***@{domain}'


def ensure_fay_schema(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        conn.execute('''CREATE TABLE IF NOT EXISTS T_Msg
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
            type CHAR(10), way CHAR(10), content TEXT NOT NULL,
            createtime INT, username TEXT DEFAULT 'User', uid INT,
            images TEXT, session_id INTEGER DEFAULT NULL, topic TEXT DEFAULT '')''')
        _ensure_columns(conn, 'T_Msg', {
            'images': 'TEXT',
            'session_id': 'INTEGER DEFAULT NULL',
            'topic': 'TEXT DEFAULT ""',
        })
        conn.execute('''CREATE TABLE IF NOT EXISTS T_ServiceSession
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER, username TEXT, started_at INTEGER,
            last_active_at INTEGER, message_count INTEGER DEFAULT 0,
            source TEXT DEFAULT 'chat')''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_msg_createtime ON T_Msg(createtime)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_msg_topic ON T_Msg(topic)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_msg_uid ON T_Msg(uid)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_msg_session ON T_Msg(session_id)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_msg_username ON T_Msg(username)')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_session_started ON T_ServiceSession(started_at)')
        conn.commit()
    finally:
        conn.close()


def _ensure_columns(conn, table, definitions):
    existing = {row[1] for row in conn.execute(f'PRAGMA table_info({table})').fetchall()}
    for name, definition in definitions.items():
        if name not in existing:
            conn.execute(f'ALTER TABLE {table} ADD COLUMN {name} {definition}')


def range_start_ms(range_key):
    now = datetime.now()
    today = datetime(now.year, now.month, now.day)
    if range_key == '30d':
        return int((today - timedelta(days=29)).timestamp() * 1000)
    if range_key == 'week':
        return int((today - timedelta(days=today.weekday())).timestamp() * 1000)
    if range_key == 'month':
        return int(datetime(now.year, now.month, 1).timestamp() * 1000)
    return int((today - timedelta(days=6)).timestamp() * 1000)


def today_start_ms():
    now = datetime.now()
    return int(datetime(now.year, now.month, now.day).timestamp() * 1000)


def week_start_ms():
    now = datetime.now()
    today = datetime(now.year, now.month, now.day)
    return int((today - timedelta(days=today.weekday())).timestamp() * 1000)


def fetch_member_messages(db_path, start_ms=0):
    ensure_fay_schema(db_path)
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(
            '''SELECT id, content, createtime, username, COALESCE(uid, 0), COALESCE(topic, '')
            FROM T_Msg WHERE type != 'fay' AND createtime >= ? ORDER BY createtime ASC, id ASC''',
            (int(start_ms or 0),),
        ).fetchall()
    finally:
        conn.close()


def derive_sessions(messages):
    sessions = []
    active = {}
    for _msg_id, content, created_ms, username, uid, _topic in messages:
        if not content:
            continue
        key = uid or username or 'anonymous'
        previous = active.get(key)
        if previous is None or created_ms - previous['last_active_at'] > SESSION_TIMEOUT_MS:
            previous = {'key': key, 'username': username, 'started_at': created_ms, 'last_active_at': created_ms, 'message_count': 0}
            sessions.append(previous)
        previous['last_active_at'] = created_ms
        previous['message_count'] += 1
        active[key] = previous
    return sessions


def operational_summary(db_path, range_key='7d'):
    start_ms = min(range_start_ms(range_key), week_start_ms(), today_start_ms())
    messages = fetch_member_messages(db_path, start_ms)
    sessions = derive_sessions(messages)
    today_ms = today_start_ms()
    week_ms = week_start_ms()
    return {
        'today_services': sum(1 for item in sessions if item['started_at'] >= today_ms),
        'week_services': sum(1 for item in sessions if item['started_at'] >= week_ms),
        'today_questions': sum(1 for item in messages if item[2] >= today_ms),
        'week_active_users': len({item[4] or item[3] for item in messages if item[2] >= week_ms}),
        'message_count': len(messages),
        'session_count': len(sessions),
    }


def service_trends(db_path, range_key='7d'):
    start_ms = range_start_ms(range_key)
    messages = fetch_member_messages(db_path, start_ms)
    sessions = derive_sessions(messages)
    labels = _date_labels(start_ms)
    question_counts = Counter(_date_from_ms(item[2]) for item in messages)
    session_counts = Counter(_date_from_ms(item['started_at']) for item in sessions)
    users_by_day = defaultdict(set)
    for _msg_id, _content, created_ms, username, uid, _topic in messages:
        users_by_day[_date_from_ms(created_ms)].add(uid or username)
    return [
        {
            'date': label,
            'services': session_counts[label],
            'questions': question_counts[label],
            'active_users': len(users_by_day[label]),
        }
        for label in labels
    ]


def hot_topics(db_path, range_key='7d', limit=8):
    messages = fetch_member_messages(db_path, range_start_ms(range_key))
    counts = Counter()
    examples = {}
    for _msg_id, content, _created_ms, _username, _uid, topic in messages:
        actual_topic = topic or classify_question_topic(content)
        counts[actual_topic] += 1
        examples.setdefault(actual_topic, content)
    total = sum(counts.values()) or 1
    return [
        {
            'topic': topic,
            'count': count,
            'ratio': round(count / total, 4),
            'representative_question': examples.get(topic, ''),
            'trend': 0,
        }
        for topic, count in counts.most_common(limit)
    ]


def _date_labels(start_ms):
    start = datetime.fromtimestamp(start_ms / 1000).date()
    end = datetime.now().date()
    days = max(1, (end - start).days + 1)
    return [(start + timedelta(days=index)).isoformat() for index in range(days)]


def _date_from_ms(value):
    return datetime.fromtimestamp((value or 0) / 1000).date().isoformat()


def _date_from_seconds(value):
    return datetime.fromtimestamp(int(value or 0)).date().isoformat()


def _user_trend(rows, timestamp_index):
    labels = _date_labels(range_start_ms('7d'))
    counts = Counter(_date_from_seconds(row[timestamp_index]) for row in rows if row[timestamp_index])
    return [{'date': label, 'count': counts[label]} for label in labels]


def user_metrics(db_path, is_admin=False):
    if not os.path.exists(db_path):
        return _empty_user_metrics()
    conn = sqlite3.connect(db_path)
    try:
        if not _table_exists(conn, 'T_Member'):
            return _empty_user_metrics()
        rows = _fetch_member_rows(conn)
    finally:
        conn.close()
    now = int(time.time())
    today = int(today_start_ms() / 1000)
    week = int(week_start_ms() / 1000)
    role_counts = Counter(row[2] or 'user' for row in rows)
    registration_trend = _user_trend(rows, 4)
    active_trend = _user_trend(rows, 5)
    return {
        'total_users': len(rows),
        'today_new_users': sum(1 for row in rows if (row[4] or 0) >= today),
        'week_new_users': sum(1 for row in rows if (row[4] or 0) >= week),
        'week_active_users': sum(1 for row in rows if (row[5] or 0) >= week),
        'active_users': sum(1 for row in rows if int(row[6] or 0) == 1),
        'role_distribution': [{'role': key, 'count': value} for key, value in role_counts.items()],
        'registration_trend': registration_trend,
        'active_trend': active_trend,
        'recent_users': [_public_user(row, is_admin) for row in rows[:10]],
        'server_time': now,
    }


def _fetch_member_rows(conn):
    cursor = conn.execute('PRAGMA table_info(T_Member)')
    columns = {row[1] for row in cursor.fetchall()}
    select_parts = [
        'id',
        'username',
        _column_or_default(columns, 'role', "'user'"),
        _column_or_default(columns, 'email', "''"),
        _column_or_default(columns, 'created_at', '0'),
        _column_or_default(columns, 'last_login', '0'),
        _column_or_default(columns, 'is_active', '1'),
    ]
    sort_expr = _sort_expression(columns)
    return conn.execute(f'SELECT {", ".join(select_parts)} FROM T_Member ORDER BY {sort_expr}, id ASC').fetchall()


def _column_or_default(columns, name, default_sql):
    if name in columns:
        return name
    return f'{default_sql} AS {name}'


def _sort_expression(columns):
    if 'last_login' in columns and 'created_at' in columns:
        return 'COALESCE(last_login, created_at, 0) DESC'
    if 'last_login' in columns:
        return 'COALESCE(last_login, 0) DESC'
    if 'created_at' in columns:
        return 'COALESCE(created_at, 0) DESC'
    return 'id DESC'


def _table_exists(conn, table):
    row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()
    return row is not None


def _public_user(row, is_admin):
    uid, username, role, email, created_at, last_login, is_active = row
    return {
        'uid': uid,
        'username': username,
        'role': role or 'user',
        'email': email if is_admin else mask_email(email),
        'created_at': created_at,
        'last_login': last_login,
        'is_active': is_active,
    }


def _empty_user_metrics():
    labels = _date_labels(range_start_ms('7d'))
    return {
        'total_users': 0, 'today_new_users': 0, 'week_new_users': 0,
        'week_active_users': 0, 'active_users': 0, 'role_distribution': [],
        'registration_trend': [{'date': label, 'count': 0} for label in labels],
        'active_trend': [{'date': label, 'count': 0} for label in labels],
        'recent_users': [], 'server_time': int(time.time()),
    }
