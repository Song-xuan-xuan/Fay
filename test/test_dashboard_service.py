import os
import sqlite3
import sys
import tempfile
import time
import types
import unittest

from openpyxl import Workbook


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.dashboard_service import DashboardPaths, DashboardService, classify_question_topic, mask_email


HEADERS = [
    'tourist_id',
    'user_nickname',
    'age',
    'gender',
    'attraction_name',
    'attraction_content',
    'attraction_type',
    'visit_date',
    'stay_duration',
    'ticket_cost',
    'food_cost',
    'shopping_cost',
    'transport_cost',
    'entertainment_cost',
    'total_cost',
    'group_size',
    'satisfaction',
]


class DashboardServiceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = self.tmp.name
        self.paths = DashboardPaths(
            project_root=root,
            fay_db_path=os.path.join(root, 'memory', 'fay.db'),
            user_db_path=os.path.join(root, 'memory', 'user_profiles.db'),
            tourism_db_path=os.path.join(root, 'memory', 'tourism.db'),
            tourism_excel_path=os.path.join(root, 'data', 'tourism.xlsx'),
        )
        os.makedirs(os.path.join(root, 'data'), exist_ok=True)
        os.makedirs(os.path.join(root, 'memory'), exist_ok=True)

    def tearDown(self):
        self.tmp.cleanup()

    def _write_excel(self):
        wb = Workbook()
        ws = wb.active
        ws.append(HEADERS)
        ws.append(['U1', '游客A', 31, '女', '湖心公园', '介绍', '自然公园', '2025-01-01', 2.5, 30, 20, 10, 5, 8, 73, 2, 5])
        ws.append(['U2', '游客B', 42, '男', '欢乐世界', '介绍', '主题乐园', '2025-01-02', 4, 90, 50, 30, 12, 40, 222, 4, 2])
        ws.append(['U3', '游客C', 24, '女', '欢乐世界', '介绍', '主题乐园', '2025-02-01', 3, 90, 30, 18, 10, 20, 168, 1, 4])
        wb.save(self.paths.tourism_excel_path)

    def _write_user_db(self):
        conn = sqlite3.connect(self.paths.user_db_path)
        conn.execute(
            '''CREATE TABLE T_Member (
                id INTEGER PRIMARY KEY,
                username TEXT,
                extra_info TEXT,
                user_portrait TEXT,
                password_hash TEXT,
                role TEXT,
                email TEXT,
                created_at INTEGER,
                last_login INTEGER,
                is_active INTEGER,
                password_changed_at INTEGER
            )'''
        )
        now = int(time.time())
        conn.execute(
            'INSERT INTO T_Member VALUES (1, ?, "", "", "hash", ?, ?, ?, ?, 1, ?)',
            ('alice', 'admin', 'alice@example.com', now, now, now),
        )
        conn.commit()
        conn.close()

    def _write_legacy_user_db(self):
        conn = sqlite3.connect(self.paths.user_db_path)
        conn.execute(
            '''CREATE TABLE T_Member (
                id INTEGER PRIMARY KEY,
                username TEXT,
                extra_info TEXT,
                user_portrait TEXT
            )'''
        )
        conn.execute('INSERT INTO T_Member VALUES (1, ?, "", "")', ('legacy-user',))
        conn.commit()
        conn.close()

    def test_classifies_common_question_topics(self):
        self.assertEqual('门票开放', classify_question_topic('门票多少钱，几点开放'))
        self.assertEqual('交通路线', classify_question_topic('坐地铁怎么去景区'))
        self.assertEqual('餐饮购物', classify_question_topic('附近有什么餐厅和纪念品'))
        self.assertEqual('其他问题', classify_question_topic('你好'))

    def test_imports_tourism_excel_and_returns_dashboard_metrics(self):
        self._write_excel()
        service = DashboardService(self.paths)
        result = service.import_tourism_excel(force=True)
        tourism = service.get_tourism({})
        filtered = service.get_tourism({
            'tourist_segment': '18-29岁',
            'satisfaction_min': '3',
            'satisfaction_max': '5',
        })

        self.assertEqual(3, result['row_count'])
        self.assertEqual(3, tourism['source']['record_count'])
        self.assertEqual('success', tourism['source']['import_status'])
        self.assertEqual('2025-01-01', tourism['source']['date_range']['start'])
        self.assertEqual('2025-02-01', tourism['source']['date_range']['end'])
        self.assertEqual('主题乐园', tourism['type_metrics'][0]['name'])
        self.assertEqual(1, tourism['low_satisfaction_count'])
        self.assertEqual({'month': '2025-01', 'visits': 2, 'tourists': 2}, tourism['visit_trend'][0])
        self.assertEqual('高满意', tourism['satisfaction_distribution'][-1]['name'])
        self.assertEqual(4, filtered['details'][0]['satisfaction'])
        self.assertEqual('18-29岁', filtered['details'][0]['tourist_segment'])

    def test_user_metrics_mask_sensitive_email_for_non_admin(self):
        self._write_user_db()
        service = DashboardService(self.paths)
        users = service.get_user_metrics(is_admin=False)

        self.assertEqual('a***@example.com', mask_email('alice@example.com'))
        self.assertEqual(1, users['total_users'])
        self.assertEqual('a***@example.com', users['recent_users'][0]['email'])
        self.assertNotIn('password_hash', users['recent_users'][0])
        self.assertEqual(7, len(users['registration_trend']))
        self.assertEqual(7, len(users['active_trend']))

    def test_user_metrics_support_legacy_member_schema(self):
        self._write_legacy_user_db()
        service = DashboardService(self.paths)
        users = service.get_user_metrics(is_admin=False)

        self.assertEqual(1, users['total_users'])
        self.assertEqual('legacy-user', users['recent_users'][0]['username'])
        self.assertEqual('user', users['recent_users'][0]['role'])
        self.assertEqual('', users['recent_users'][0]['email'])

    def test_user_messages_persist_service_session_ids(self):
        previous_cwd = os.getcwd()
        os.chdir(self.paths.project_root)
        previous_util = sys.modules.get('utils.util')
        sys.modules['utils.util'] = types.SimpleNamespace(log=lambda *_args, **_kwargs: None, ms_to_timetext=lambda value: str(value))
        try:
            sys.modules.pop('core.content_db', None)
            from core.content_db import Content_Db

            db = Content_Db()
            db.init_db()
            first_id, _ = db.add_content('member', 'speak', '门票多少钱', 'alice', 1, created_ms=1_000)
            second_id, _ = db.add_content('member', 'speak', '几点开放', 'alice', 1, created_ms=1_000 + 60_000)
            third_id, _ = db.add_content('member', 'speak', '怎么停车', 'alice', 1, created_ms=1_000 + 32 * 60_000)

            conn = sqlite3.connect(self.paths.fay_db_path)
            rows = conn.execute('SELECT id, session_id, topic FROM T_Msg ORDER BY id').fetchall()
            session_count = conn.execute('SELECT COUNT(*) FROM T_ServiceSession').fetchone()[0]
            conn.close()
        finally:
            sys.modules.pop('core.content_db', None)
            if previous_util is None:
                sys.modules.pop('utils.util', None)
            else:
                sys.modules['utils.util'] = previous_util
            os.chdir(previous_cwd)

        self.assertEqual([first_id, second_id, third_id], [row[0] for row in rows])
        self.assertEqual(rows[0][1], rows[1][1])
        self.assertNotEqual(rows[0][1], rows[2][1])
        self.assertEqual('门票开放', rows[0][2])
        self.assertEqual(2, session_count)

    def test_operational_metrics_use_persisted_service_sessions(self):
        now_ms = int(time.time() * 1000)
        conn = sqlite3.connect(self.paths.fay_db_path)
        conn.execute(
            '''CREATE TABLE T_Msg (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT, way TEXT, content TEXT NOT NULL,
                createtime INTEGER, username TEXT, uid INTEGER,
                images TEXT, session_id INTEGER, topic TEXT
            )'''
        )
        conn.execute(
            '''CREATE TABLE T_ServiceSession (
                id INTEGER PRIMARY KEY,
                user_id INTEGER, username TEXT, started_at INTEGER,
                last_active_at INTEGER, message_count INTEGER DEFAULT 0,
                source TEXT DEFAULT 'chat', deleted_at INTEGER DEFAULT NULL
            )'''
        )
        conn.executemany(
            '''INSERT INTO T_ServiceSession
            (id, user_id, username, started_at, last_active_at, message_count, source, deleted_at)
            VALUES (?, 1, 'alice', ?, ?, 1, 'chat', NULL)''',
            [(10, now_ms - 60_000, now_ms - 60_000), (11, now_ms, now_ms)],
        )
        conn.executemany(
            '''INSERT INTO T_Msg
            (type, way, content, createtime, username, uid, images, session_id, topic)
            VALUES ('member', 'text', ?, ?, 'alice', 1, NULL, ?, '')''',
            [('门票多少钱', now_ms - 60_000, 10), ('怎么停车', now_ms, 11)],
        )
        conn.commit()
        conn.close()

        service = DashboardService(self.paths)
        summary = service.get_overview('7d')['operations']
        trends = service.get_service_trends('7d')['items']

        self.assertEqual(2, summary['session_count'])
        self.assertEqual(2, summary['today_services'])
        self.assertEqual(2, trends[-1]['services'])


if __name__ == '__main__':
    unittest.main()
