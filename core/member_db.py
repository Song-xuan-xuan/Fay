import functools
import os
import sqlite3
import threading
import time

import bcrypt


DB_PATH = os.path.join('memory', 'user_profiles.db')
USER_COLUMNS = (
    'id',
    'username',
    'extra_info',
    'user_portrait',
    'password_hash',
    'role',
    'email',
    'avatar_path',
    'created_at',
    'last_login',
    'is_active',
    'password_changed_at',
)


def synchronized(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        with self.lock:
            return func(self, *args, **kwargs)
    return wrapper


__member_db = None


def new_instance():
    global __member_db
    if __member_db is None:
        __member_db = Member_Db()
        __member_db.init_db()
    return __member_db


class Member_Db:
    def __init__(self) -> None:
        self.lock = threading.RLock()

    def _connect(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        return sqlite3.connect(DB_PATH)

    def init_db(self):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS T_Member
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            extra_info TEXT DEFAULT '',
            user_portrait TEXT DEFAULT '',
            password_hash TEXT NOT NULL DEFAULT '',
            role TEXT NOT NULL DEFAULT 'user',
            email TEXT DEFAULT '',
            avatar_path TEXT DEFAULT '',
            created_at INTEGER,
            last_login INTEGER,
            is_active INTEGER DEFAULT 1,
            password_changed_at INTEGER DEFAULT NULL);''')
        self._ensure_columns(cursor)
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_member_username ON T_Member(username)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_member_role ON T_Member(role)')
        cursor.execute('INSERT OR IGNORE INTO T_Member (username, created_at) VALUES (?, ?)', ('User', int(time.time())))
        conn.commit()
        conn.close()

    def _ensure_columns(self, cursor):
        cursor.execute('PRAGMA table_info(T_Member)')
        existing = {column[1] for column in cursor.fetchall()}
        definitions = {
            'extra_info': 'TEXT DEFAULT ""',
            'user_portrait': 'TEXT DEFAULT ""',
            'password_hash': 'TEXT NOT NULL DEFAULT ""',
            'role': 'TEXT NOT NULL DEFAULT "user"',
            'email': 'TEXT DEFAULT ""',
            'avatar_path': 'TEXT DEFAULT ""',
            'created_at': 'INTEGER',
            'last_login': 'INTEGER',
            'is_active': 'INTEGER DEFAULT 1',
            'password_changed_at': 'INTEGER DEFAULT NULL',
        }
        for name, definition in definitions.items():
            if name not in existing:
                cursor.execute(f'ALTER TABLE T_Member ADD COLUMN {name} {definition}')

    def _hash_password(self, password):
        return bcrypt.hashpw(str(password).encode(), bcrypt.gensalt()).decode()

    def _row_to_user(self, row, include_hash=True):
        if row is None:
            return None
        user = dict(zip(('uid', *USER_COLUMNS[1:]), row))
        if not include_hash:
            user.pop('password_hash', None)
        return user

    def _select_user_sql(self):
        return ', '.join(USER_COLUMNS)

    def _fetch_user(self, column, value, include_hash=True):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(f'SELECT {self._select_user_sql()} FROM T_Member WHERE {column} = ?', (value,))
        user = self._row_to_user(cursor.fetchone(), include_hash=include_hash)
        conn.close()
        return user

    @synchronized
    def add_user(self, username):
        if self.is_username_exist(username) != 'notexists':
            return f"Username '{username}' already exists."
        conn = self._connect()
        conn.execute('INSERT INTO T_Member (username, created_at) VALUES (?, ?)', (username, int(time.time())))
        conn.commit()
        conn.close()
        return 'success'

    @synchronized
    def update_user(self, username, new_username):
        if self.is_username_exist(new_username) != 'notexists':
            return f"Username '{new_username}' already exists."
        conn = self._connect()
        conn.execute('UPDATE T_Member SET username = ? WHERE username = ?', (new_username, username))
        conn.commit()
        conn.close()
        return 'success'

    @synchronized
    def delete_user(self, username):
        conn = self._connect()
        conn.execute('DELETE FROM T_Member WHERE username = ?', (username,))
        conn.commit()
        conn.close()
        return 'success'

    def is_username_exist(self, username):
        conn = self._connect()
        count = conn.execute('SELECT COUNT(*) FROM T_Member WHERE username = ?', (username,)).fetchone()[0]
        conn.close()
        return 'exists' if count > 0 else 'notexists'

    def find_user(self, username):
        user = self.get_user_by_username(username)
        return user['uid'] if user else 0

    def find_username_by_uid(self, uid):
        user = self.get_user_by_uid(uid)
        return user['username'] if user else 0

    def get_user_by_username(self, username, include_hash=True):
        return self._fetch_user('username', username, include_hash=include_hash)

    def get_user_by_uid(self, uid, include_hash=True):
        return self._fetch_user('id', uid, include_hash=include_hash)

    def get_extra_info(self, username):
        user = self.get_user_by_username(username)
        return user['extra_info'] if user and user['extra_info'] else ''

    @synchronized
    def update_extra_info(self, username, extra_info):
        conn = self._connect()
        conn.execute('UPDATE T_Member SET extra_info = ? WHERE username = ?', (extra_info, username))
        conn.commit()
        conn.close()
        return 'success'

    def get_user_portrait(self, username):
        user = self.get_user_by_username(username)
        return user['user_portrait'] if user and user['user_portrait'] else ''

    @synchronized
    def update_user_portrait(self, username, user_portrait):
        conn = self._connect()
        conn.execute('UPDATE T_Member SET user_portrait = ? WHERE username = ?', (user_portrait, username))
        conn.commit()
        conn.close()
        return 'success'

    @synchronized
    def update_avatar_path(self, uid, avatar_path):
        conn = self._connect()
        conn.execute('UPDATE T_Member SET avatar_path = ? WHERE id = ?', (avatar_path or '', uid))
        conn.commit()
        conn.close()
        return self.get_user_by_uid(uid, include_hash=False)

    @synchronized
    def query(self, sql):
        try:
            conn = self._connect()
            results = conn.execute(sql).fetchall()
            conn.commit()
            conn.close()
            return results
        except Exception as exc:
            return f'执行时发生错误：{str(exc)}'

    @synchronized
    def get_all_users(self):
        self.init_db()
        conn = self._connect()
        results = conn.execute(f'SELECT {self._select_user_sql()} FROM T_Member ORDER BY id ASC').fetchall()
        conn.close()
        return results

    @synchronized
    def create_default_admin(self, username, password):
        user = self.get_user_by_username(username)
        if not user:
            return self.create_user_with_password(username, password, role='admin')
        self.reset_password(user['uid'], password, force_change=True)
        self.update_user_auth(user['uid'], role='admin', is_active=True)
        return self.get_user_by_uid(user['uid'])

    def has_admin_user(self):
        conn = self._connect()
        count = conn.execute("SELECT COUNT(*) FROM T_Member WHERE role = 'admin' AND is_active = 1").fetchone()[0]
        conn.close()
        return count > 0

    @synchronized
    def create_user_with_password(self, username, password, *, role='user', email='', force_change=True):
        now = int(time.time())
        changed_at = None if force_change else now
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO T_Member
            (username, password_hash, role, email, created_at, is_active, password_changed_at)
            VALUES (?, ?, ?, ?, ?, 1, ?)''',
            (username, self._hash_password(password), role, email, now, changed_at),
        )
        uid = cursor.lastrowid
        conn.commit()
        conn.close()
        return self.get_user_by_uid(uid)

    @synchronized
    def update_user_auth(self, uid, *, role=None, email=None, is_active=None):
        fields = []
        values = []
        for name, value in (('role', role), ('email', email), ('is_active', is_active)):
            if value is not None:
                fields.append(f'{name} = ?')
                values.append(int(value) if name == 'is_active' else value)
        if not fields:
            return self.get_user_by_uid(uid)
        conn = self._connect()
        conn.execute(f'UPDATE T_Member SET {", ".join(fields)} WHERE id = ?', (*values, uid))
        conn.commit()
        conn.close()
        return self.get_user_by_uid(uid)

    @synchronized
    def reset_password(self, uid, new_password, force_change=True):
        changed_at = None if force_change else int(time.time())
        conn = self._connect()
        conn.execute(
            'UPDATE T_Member SET password_hash = ?, password_changed_at = ? WHERE id = ?',
            (self._hash_password(new_password), changed_at, uid),
        )
        conn.commit()
        conn.close()
        return 'success'

    @synchronized
    def change_password(self, username, old_password, new_password):
        if not self.verify_password(username, old_password):
            return False
        user = self.get_user_by_username(username)
        self.reset_password(user['uid'], new_password, force_change=False)
        return True

    def verify_password(self, username, password):
        user = self.get_user_by_username(username)
        if not user or not user['password_hash'] or int(user['is_active'] or 0) != 1:
            return False
        return bcrypt.checkpw(str(password).encode(), user['password_hash'].encode())

    def must_change_password(self, username):
        user = self.get_user_by_username(username)
        return bool(user and user['password_changed_at'] is None)

    @synchronized
    def touch_last_login(self, uid):
        conn = self._connect()
        conn.execute('UPDATE T_Member SET last_login = ? WHERE id = ?', (int(time.time()), uid))
        conn.commit()
        conn.close()

    def list_users(self):
        conn = self._connect()
        rows = conn.execute(f'SELECT {self._select_user_sql()} FROM T_Member ORDER BY id ASC').fetchall()
        conn.close()
        return [self._row_to_user(row, include_hash=False) for row in rows]
