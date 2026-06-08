import sqlite3
import time
import threading
import functools
from utils import util

try:
    from core.dashboard_operational import SESSION_TIMEOUT_MS, classify_question_topic
except Exception:
    SESSION_TIMEOUT_MS = 30 * 60 * 1000
    classify_question_topic = None

def synchronized(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        with self.lock:
            return func(self, *args, **kwargs)
    return wrapper

__content_tb = None
def new_instance():
    global __content_tb
    if __content_tb is None:
        __content_tb = Content_Db()
        __content_tb.init_db()
    return __content_tb

class Content_Db:

    def __init__(self) -> None:
        self.lock = threading.RLock()

    # 初始化数据库
    def init_db(self):
        conn = sqlite3.connect('memory/fay.db')
        conn.text_factory = str
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS T_Msg
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
            type        CHAR(10),
            way         CHAR(10),
            content     TEXT    NOT NULL,
            createtime  INT,
            username    TEXT DEFAULT 'User',
            uid         INT,
            images      TEXT);''')

        self._ensure_message_columns(c)
        self._ensure_service_session_table(c)

        # 对话采纳记录表
        c.execute('''CREATE TABLE IF NOT EXISTS T_Adopted
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
            msg_id      INTEGER UNIQUE,
            adopted_time INT,
            FOREIGN KEY(msg_id) REFERENCES T_Msg(id));''')
        conn.commit()
        conn.close()

    def _ensure_message_columns(self, cursor):
        cursor.execute('PRAGMA table_info(T_Msg)')
        existing = {column[1] for column in cursor.fetchall()}
        definitions = {
            'images': 'TEXT',
            'session_id': 'INTEGER DEFAULT NULL',
            'topic': 'TEXT DEFAULT ""',
        }
        for name, definition in definitions.items():
            if name not in existing:
                try:
                    cursor.execute(f'ALTER TABLE T_Msg ADD COLUMN {name} {definition}')
                    util.log(1, f'数据库升级：T_Msg 表已添加 {name} 字段')
                except Exception as e:
                    util.log(1, f'添加 {name} 字段失败（可能已存在）: {e}')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_msg_createtime ON T_Msg(createtime)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_msg_topic ON T_Msg(topic)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_msg_uid ON T_Msg(uid)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_msg_session ON T_Msg(session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_msg_username ON T_Msg(username)')

    def _ensure_service_session_table(self, cursor):
        cursor.execute('''CREATE TABLE IF NOT EXISTS T_ServiceSession
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            username    TEXT,
            started_at  INTEGER,
            last_active_at INTEGER,
            message_count INTEGER DEFAULT 0,
            source      TEXT DEFAULT 'chat',
            title       TEXT DEFAULT '',
            deleted_at  INTEGER DEFAULT NULL);''')
        self._ensure_session_columns(cursor)
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_started ON T_ServiceSession(started_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_user ON T_ServiceSession(user_id)')

    def _ensure_session_columns(self, cursor):
        cursor.execute('PRAGMA table_info(T_ServiceSession)')
        existing = {column[1] for column in cursor.fetchall()}
        definitions = {
            'title': 'TEXT DEFAULT ""',
            'deleted_at': 'INTEGER DEFAULT NULL',
        }
        for name, definition in definitions.items():
            if name not in existing:
                cursor.execute(f'ALTER TABLE T_ServiceSession ADD COLUMN {name} {definition}')

    # 添加对话
    @synchronized
    def add_content(self, type, way, content, username='User', uid=0, images=None, created_ms=None, session_id=None):
        """
        添加对话消息

        Args:
            type: 消息类型
            way: 来源
            content: 文本内容
            username: 用户名
            uid: 用户ID
            images: 图片URL列表（可选）
            created_ms: 指定创建时间，主要用于测试或导入历史消息

        Returns:
            (last_id, now_ms)
        """
        import json
        conn = sqlite3.connect("memory/fay.db")
        conn.text_factory = str
        cur = conn.cursor()
        now_ms = int(created_ms if created_ms is not None else time.time() * 1000)

        # 将图片列表转为 JSON
        images_json = json.dumps(images) if images else None
        topic = ''
        active_session_id = None
        if session_id is not None:
            requested_session_id = int(session_id)
            if requested_session_id != 0:
                active_session_id = requested_session_id
                self._touch_service_session(cur, active_session_id, now_ms, increment=(type != 'fay'))
        elif type != 'fay':
            if classify_question_topic:
                topic = classify_question_topic(content)
            active_session_id = self._upsert_service_session(cur, username, uid, now_ms)

        try:
            cur.execute("""INSERT INTO T_Msg
                (type, way, content, createtime, username, uid, images, session_id, topic)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (type, way, content, now_ms, username, uid, images_json, active_session_id, topic))
            conn.commit()
            last_id = cur.lastrowid
        except Exception as e:
            util.log(1, "请检查参数是否有误: {}".format(e))
            conn.close()
            return 0, 0
        conn.close()
        return last_id, now_ms

    def _upsert_service_session(self, cursor, username, uid, now_ms):
        session = self._find_active_service_session(cursor, username, uid, now_ms)
        if session:
            session_id, message_count = session
            cursor.execute(
                'UPDATE T_ServiceSession SET last_active_at = ?, message_count = ? WHERE id = ?',
                (now_ms, int(message_count or 0) + 1, session_id),
            )
            return session_id
        cursor.execute(
            '''INSERT INTO T_ServiceSession
            (user_id, username, started_at, last_active_at, message_count, source)
            VALUES (?, ?, ?, ?, 1, 'chat')''',
            (int(uid or 0), username or 'User', now_ms, now_ms),
        )
        return cursor.lastrowid

    def _touch_service_session(self, cursor, session_id, now_ms, increment=False):
        if increment:
            cursor.execute(
                '''UPDATE T_ServiceSession
                SET last_active_at = ?, message_count = message_count + 1
                WHERE id = ? AND deleted_at IS NULL''',
                (now_ms, int(session_id)),
            )
            return
        cursor.execute(
            'UPDATE T_ServiceSession SET last_active_at = ? WHERE id = ? AND deleted_at IS NULL',
            (now_ms, int(session_id)),
        )

    def _find_active_service_session(self, cursor, username, uid, now_ms):
        if int(uid or 0) != 0:
            row = cursor.execute(
                '''SELECT id, message_count, last_active_at FROM T_ServiceSession
                WHERE user_id = ? AND deleted_at IS NULL ORDER BY last_active_at DESC LIMIT 1''',
                (int(uid),),
            ).fetchone()
        else:
            row = cursor.execute(
                '''SELECT id, message_count, last_active_at FROM T_ServiceSession
                WHERE username = ? AND deleted_at IS NULL ORDER BY last_active_at DESC LIMIT 1''',
                (username or 'User',),
            ).fetchone()
        if not row:
            return None
        session_id, message_count, last_active_at = row
        if now_ms - int(last_active_at or 0) > SESSION_TIMEOUT_MS:
            return None
        return session_id, message_count

    # 更新对话内容
    @synchronized
    def update_content(self, msg_id, content):
        """
        更新指定ID的消息内容，同时更新时间为当前时间
        :param msg_id: 消息ID
        :param content: 新的内容
        :return: 更新后的毫秒时间戳，失败返回0
        """
        conn = sqlite3.connect("memory/fay.db")
        conn.text_factory = str
        cur = conn.cursor()
        now_ms = int(time.time() * 1000)
        try:
            cur.execute("UPDATE T_Msg SET content = ?, createtime = ? WHERE id = ?", (content, now_ms, msg_id))
            conn.commit()
            affected_rows = cur.rowcount
        except Exception as e:
            util.log(1, f"更新消息内容失败: {e}")
            conn.close()
            return 0
        conn.close()
        return now_ms if affected_rows > 0 else 0

    # 根据ID查询对话记录
    @synchronized
    def get_content_by_id(self, msg_id):
        conn = sqlite3.connect("memory/fay.db")
        conn.text_factory = str
        cur = conn.cursor()
        cur.execute("SELECT * FROM T_Msg WHERE id = ?", (msg_id,))
        record = cur.fetchone()
        conn.close()
        return record

    # 添加对话采纳记录
    @synchronized
    def adopted_message(self, msg_id):
        conn = sqlite3.connect('memory/fay.db')
        conn.text_factory = str
        cur = conn.cursor()
        # 检查消息ID是否存在
        cur.execute("SELECT 1 FROM T_Msg WHERE id = ?", (msg_id,))
        if cur.fetchone() is None:
            util.log(1, "消息ID不存在")
            conn.close()
            return False
        try:
            cur.execute("INSERT INTO T_Adopted (msg_id, adopted_time) VALUES (?, ?)", (msg_id, int(time.time())))
            conn.commit()
        except sqlite3.IntegrityError:
            util.log(1, "该消息已被采纳")
            conn.close()
            return False
        conn.close()
        return True

    # 取消采纳：删除采纳记录并返回相同clean_content的所有消息ID
    @synchronized
    def unadopt_message(self, msg_id, clean_content):
        """
        取消采纳消息
        :param msg_id: 消息ID
        :param clean_content: 过滤掉think标签后的干净内容，用于匹配QA文件
        :return: (success, same_content_ids)
        """
        import re
        conn = sqlite3.connect('memory/fay.db')
        conn.text_factory = str
        cur = conn.cursor()

        # 获取所有fay类型的消息，检查过滤think后的内容是否匹配
        cur.execute("SELECT id, content FROM T_Msg WHERE type = 'fay'")
        all_fay_msgs = cur.fetchall()

        # 规范化目标内容：去掉换行符和首尾空格
        clean_content_normalized = clean_content.replace('\n', '').replace('\r', '').strip()

        same_content_ids = []
        for row in all_fay_msgs:
            row_id, row_content = row
            # 过滤掉think标签内容后比较
            row_clean = re.sub(r'<think>[\s\S]*?</think>', '', row_content, flags=re.IGNORECASE).strip()
            # 规范化后比较
            row_clean_normalized = row_clean.replace('\n', '').replace('\r', '').strip()
            if row_clean_normalized == clean_content_normalized:
                same_content_ids.append(row_id)

        # 删除这些消息的采纳记录
        if same_content_ids:
            placeholders = ','.join('?' * len(same_content_ids))
            cur.execute(f"DELETE FROM T_Adopted WHERE msg_id IN ({placeholders})", same_content_ids)
            conn.commit()

        conn.close()
        return True, same_content_ids

    # 获取对话内容
    @synchronized
    def get_list(self, way, order, limit, uid=0, offset=0, session_id=None):
        conn = sqlite3.connect("memory/fay.db")
        conn.text_factory = str
        cur = conn.cursor()
        where_uid = ""
        if int(uid) != 0:
            where_uid = f" AND T_Msg.uid = {uid} "
        where_session = ""
        params = []
        if session_id is not None:
            if int(session_id) == 0:
                where_session = " AND T_Msg.session_id IS NULL "
            else:
                where_session = " AND T_Msg.session_id = ? "
                params.append(int(session_id))
        base_query = f"""
            SELECT T_Msg.type, T_Msg.way, T_Msg.content, T_Msg.createtime,
                   datetime(T_Msg.createtime/1000, 'unixepoch', 'localtime') AS timetext,
                   T_Msg.username,T_Msg.id,
                   CASE WHEN T_Adopted.msg_id IS NOT NULL THEN 1 ELSE 0 END AS is_adopted,
                   T_Msg.images,
                   T_Msg.session_id
            FROM T_Msg
            LEFT JOIN T_Adopted ON T_Msg.id = T_Adopted.msg_id
            WHERE 1 {where_uid} {where_session}
        """
        if way == 'all':
            query = base_query + f" ORDER BY T_Msg.id {order} LIMIT ? OFFSET ?"
            cur.execute(query, (*params, limit, offset))
        elif way == 'notappended':
            query = base_query + f" AND T_Msg.way != 'appended' ORDER BY T_Msg.id {order} LIMIT ? OFFSET ?"
            cur.execute(query, (*params, limit, offset))
        else:
            query = base_query + f" AND T_Msg.way = ? ORDER BY T_Msg.id {order} LIMIT ? OFFSET ?"
            cur.execute(query, (*params, way, limit, offset))
        list = cur.fetchall()
        conn.close()
        return list

    # 获取用户消息总数
    @synchronized
    def get_message_count(self, uid=0, session_id=None):
        conn = sqlite3.connect("memory/fay.db")
        conn.text_factory = str
        cur = conn.cursor()
        where = []
        params = []
        if int(uid) != 0:
            where.append("uid = ?")
            params.append(int(uid))
        if session_id is not None:
            if int(session_id) == 0:
                where.append("session_id IS NULL")
            else:
                where.append("session_id = ?")
                params.append(int(session_id))
        where_sql = f" WHERE {' AND '.join(where)}" if where else ""
        cur.execute(f"SELECT COUNT(*) FROM T_Msg {where_sql}", params)
        count = cur.fetchone()[0]
        conn.close()
        return count

    @synchronized
    def create_chat_session(self, username, uid, title='新会话'):
        conn = sqlite3.connect("memory/fay.db")
        cur = conn.cursor()
        now_ms = int(time.time() * 1000)
        cur.execute(
            '''INSERT INTO T_ServiceSession
            (user_id, username, started_at, last_active_at, message_count, source, title)
            VALUES (?, ?, ?, ?, 0, 'chat', ?)''',
            (int(uid or 0), username or 'User', now_ms, now_ms, title or '新会话'),
        )
        session_id = cur.lastrowid
        conn.commit()
        conn.close()
        return self.get_chat_session(session_id)

    @synchronized
    def get_chat_session(self, session_id):
        conn = sqlite3.connect("memory/fay.db")
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            '''SELECT id, user_id, username, started_at, last_active_at,
                   message_count, source, title, deleted_at
            FROM T_ServiceSession WHERE id = ?''',
            (int(session_id),),
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    @synchronized
    def list_chat_sessions(self, username, uid):
        conn = sqlite3.connect("memory/fay.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        rows = cursor.execute(
            '''SELECT id, user_id, username, started_at, last_active_at,
                   message_count, source, title, deleted_at
            FROM T_ServiceSession
            WHERE deleted_at IS NULL AND (user_id = ? OR username = ?)
            ORDER BY last_active_at DESC, id DESC''',
            (int(uid or 0), username or 'User'),
        ).fetchall()
        legacy_count = cursor.execute(
            'SELECT COUNT(*) FROM T_Msg WHERE uid = ? AND session_id IS NULL',
            (int(uid or 0),),
        ).fetchone()[0]
        conn.close()
        sessions = [dict(row) for row in rows]
        if legacy_count:
            sessions.append({
                'id': 0,
                'user_id': int(uid or 0),
                'username': username or 'User',
                'started_at': 0,
                'last_active_at': 0,
                'message_count': legacy_count,
                'source': 'legacy',
                'title': '默认会话',
                'deleted_at': None,
            })
        return sessions

    @synchronized
    def rename_chat_session(self, session_id, title):
        conn = sqlite3.connect("memory/fay.db")
        conn.execute(
            'UPDATE T_ServiceSession SET title = ? WHERE id = ? AND deleted_at IS NULL',
            (title or '未命名会话', int(session_id)),
        )
        conn.commit()
        conn.close()
        return self.get_chat_session(session_id)

    @synchronized
    def delete_chat_session(self, session_id, username=None, uid=0):
        conn = sqlite3.connect("memory/fay.db")
        cur = conn.cursor()
        sid = int(session_id)
        if sid == 0:
            params = []
            filters = ['session_id IS NULL']
            if int(uid or 0) != 0:
                filters.append('uid = ?')
                params.append(int(uid))
            elif username:
                filters.append('username = ?')
                params.append(username)
            cur.execute(f"SELECT id FROM T_Msg WHERE {' AND '.join(filters)}", params)
        else:
            cur.execute('SELECT id FROM T_Msg WHERE session_id = ?', (sid,))
        msg_ids = [row[0] for row in cur.fetchall()]
        if msg_ids:
            placeholders = ','.join('?' * len(msg_ids))
            cur.execute(f'DELETE FROM T_Adopted WHERE msg_id IN ({placeholders})', msg_ids)
            cur.execute(f'DELETE FROM T_Msg WHERE id IN ({placeholders})', msg_ids)
        if sid != 0:
            cur.execute('DELETE FROM T_ServiceSession WHERE id = ?', (sid,))
        conn.commit()
        conn.close()
        return len(msg_ids)
    

    @synchronized
    def get_recent_messages_by_user(self, username='User', limit=30):
        """获取用户最近的消息（包含图片）"""
        conn = sqlite3.connect("memory/fay.db")
        conn.text_factory = str
        cur = conn.cursor()
        cur.execute(
            """
            SELECT type, content, images
            FROM T_Msg
            WHERE username = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (username, limit),
        )
        rows = cur.fetchall()
        conn.close()
        rows.reverse()
        return rows

    @synchronized
    def get_recent_messages_all(self, limit=30):
        """获取所有用户的最近消息（不按用户隔离，包含图片）"""
        conn = sqlite3.connect("memory/fay.db")
        conn.text_factory = str
        cur = conn.cursor()
        cur.execute(
            """
            SELECT type, content, username, images
            FROM T_Msg
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cur.fetchall()
        conn.close()
        rows.reverse()
        return rows

    @synchronized
    def get_previous_user_message(self, msg_id):
        conn = sqlite3.connect("memory/fay.db")
        cur = conn.cursor()
        cur.execute("""
            SELECT id, type, way, content, createtime, datetime(createtime/1000, 'unixepoch', 'localtime') AS timetext, username
            FROM T_Msg
            WHERE id < ? AND type != 'fay'
            ORDER BY id DESC
            LIMIT 1
        """, (msg_id,))
        record = cur.fetchone()
        conn.close()
        return record

    # 获取指定用户当天的对话记录
    @synchronized
    def get_today_messages_by_user(self, username):
        """
        获取指定用户当天的对话记录
        :param username: 用户名
        :return: [(type, content), ...]
        """
        import datetime
        conn = sqlite3.connect("memory/fay.db")
        conn.text_factory = str
        cur = conn.cursor()
        # 获取当天0点的时间戳
        today = datetime.date.today()
        today_start = int(datetime.datetime.combine(today, datetime.time.min).timestamp() * 1000)
        cur.execute(
            """
            SELECT type, content
            FROM T_Msg
            WHERE username = ? AND createtime >= ?
            ORDER BY id ASC
            """,
            (username, today_start),
        )
        rows = cur.fetchall()
        conn.close()
        return rows

    # 删除指定用户名的所有消息
    @synchronized
    def delete_messages_by_username(self, username):
        """
        删除指定用户名的所有消息（包括用户发送的和Fay回复给该用户的）
        :param username: 用户名
        :return: 删除的消息数量
        """
        conn = sqlite3.connect("memory/fay.db")
        conn.text_factory = str
        cur = conn.cursor()
        try:
            # 先获取该用户所有消息的ID，用于删除采纳记录
            cur.execute("SELECT id FROM T_Msg WHERE username = ?", (username,))
            msg_ids = [row[0] for row in cur.fetchall()]

            # 删除这些消息的采纳记录
            if msg_ids:
                placeholders = ','.join('?' * len(msg_ids))
                cur.execute(f"DELETE FROM T_Adopted WHERE msg_id IN ({placeholders})", msg_ids)

            # 删除消息
            cur.execute("DELETE FROM T_Msg WHERE username = ?", (username,))
            deleted_count = cur.rowcount
            conn.commit()
        except Exception as e:
            util.log(1, f"删除用户消息失败: {e}")
            deleted_count = 0
        conn.close()
        return deleted_count
