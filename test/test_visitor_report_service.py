import os
import sqlite3
import sys
import tempfile
import time
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.visitor_report_service import VisitorReportPaths, VisitorReportService


def _ms(days_ago=0):
    return int((time.time() - days_ago * 24 * 60 * 60) * 1000)


class VisitorReportServiceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = self.tmp.name
        memory = os.path.join(root, 'memory')
        os.makedirs(memory, exist_ok=True)
        self.paths = VisitorReportPaths(
            fay_db_path=os.path.join(memory, 'fay.db'),
            user_db_path=os.path.join(memory, 'user_profiles.db'),
            tourism_db_path=os.path.join(memory, 'tourism.db'),
            report_db_path=os.path.join(memory, 'visitor_reports.db'),
        )
        self._write_user_db()
        self._write_fay_db()

    def tearDown(self):
        self.tmp.cleanup()

    def _write_user_db(self):
        conn = sqlite3.connect(self.paths.user_db_path)
        conn.execute(
            '''CREATE TABLE T_Member (
                id INTEGER PRIMARY KEY,
                username TEXT,
                role TEXT,
                email TEXT
            )'''
        )
        conn.execute('INSERT INTO T_Member VALUES (1, "tourist", "user", "")')
        conn.execute('INSERT INTO T_Member VALUES (2, "admin", "admin", "")')
        conn.commit()
        conn.close()

    def _write_fay_db(self):
        conn = sqlite3.connect(self.paths.fay_db_path)
        conn.execute(
            '''CREATE TABLE T_Msg (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT,
                way TEXT,
                content TEXT NOT NULL,
                createtime INTEGER,
                username TEXT,
                uid INTEGER,
                images TEXT,
                session_id INTEGER,
                topic TEXT
            )'''
        )
        rows = [
            ('member', 'text', '门票多少钱？怎么预约？', _ms(), 'tourist', 1, None, 10, ''),
            ('fay', 'text', '门票80元，可以在小程序预约。', _ms(), 'tourist', 1, None, 10, ''),
            ('member', 'text', '谢谢，明白了', _ms(), 'tourist', 1, None, 10, ''),
            ('member', 'text', '停车场坏了还收费，我要投诉', _ms(), 'tourist', 1, None, 11, ''),
            ('fay', 'text', '抱歉，我无法确认现场情况，建议联系工作人员。', _ms(), 'tourist', 1, None, 11, ''),
            ('member', 'text', '你没回答，还是不行，找人工客服', _ms(), 'tourist', 1, None, 11, ''),
            ('member', 'text', '管理员测试，不应进入报告', _ms(), 'admin', 2, None, 12, ''),
        ]
        conn.executemany(
            '''INSERT INTO T_Msg
            (type, way, content, createtime, username, uid, images, session_id, topic)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            rows,
        )
        conn.commit()
        conn.close()

    def test_analyzes_user_interactions_and_excludes_admin_messages(self):
        service = VisitorReportService(self.paths)
        items = service.analyze_interactions(range_key='7d')

        contents = [item['evidence_text'] for item in items]
        self.assertTrue(any('门票多少钱' in text for text in contents))
        self.assertFalse(any('管理员测试' in text for text in contents))

        ticket_item = next(item for item in items if '门票多少钱' in item['evidence_text'])
        complaint_item = next(item for item in items if '我要投诉' in item['evidence_text'])

        self.assertEqual('门票开放', ticket_item['topic'])
        self.assertEqual('positive', ticket_item['sentiment_label'])
        self.assertEqual('resolved', ticket_item['resolved_status'])
        self.assertEqual('服务设施', complaint_item['topic'])
        self.assertEqual('negative', complaint_item['sentiment_label'])
        self.assertEqual('high', complaint_item['risk_level'])
        self.assertEqual('escalated', complaint_item['resolved_status'])

    def test_generate_report_persists_metrics_evidence_and_actions(self):
        service = VisitorReportService(self.paths, llm_summarizer=lambda _payload: '')
        report = service.generate_report(range_key='7d', created_by='admin')
        latest = service.latest_report()
        reports = service.list_reports()
        evidence = service.get_evidence(report['id'])

        self.assertEqual(report['id'], latest['id'])
        self.assertEqual(1, len(reports))
        self.assertEqual(3, report['metrics']['message_count'])
        self.assertEqual(1, report['metrics']['complaint_count'])
        self.assertGreaterEqual(report['metrics']['negative_ratio'], 0.3)
        self.assertIn('总体结论', report['report_text'])
        self.assertIn('服务建议', report['report_text'])
        self.assertTrue(report['actions'])
        self.assertTrue(any('我要投诉' in item['evidence_text'] for item in evidence))

    def test_updates_action_status_and_exports_report(self):
        service = VisitorReportService(self.paths, llm_summarizer=lambda _payload: '')
        report = service.generate_report(range_key='7d', created_by='admin')
        action_id = report['actions'][0]['id']

        updated = service.update_action_status(action_id, 'processing')
        markdown = service.export_report(report['id'], 'md')
        html = service.export_report(report['id'], 'html')

        self.assertEqual('processing', updated['status'])
        self.assertIn('# 游客感受度报告', markdown['content'])
        self.assertIn('## 核心指标', markdown['content'])
        self.assertIn('消息量：3', markdown['content'])
        self.assertIn('投诉量：1', markdown['content'])
        self.assertIn('## 关注点分析', markdown['content'])
        self.assertIn('服务设施', markdown['content'])
        self.assertIn('## 情感与风险', markdown['content'])
        self.assertIn('## 原始依据', markdown['content'])
        self.assertIn('停车场坏了还收费，我要投诉', markdown['content'])
        self.assertIn('## 服务建议', markdown['content'])
        self.assertEqual('text/markdown; charset=utf-8', markdown['content_type'])
        self.assertIn('<h1>游客感受度报告</h1>', html['content'])
        self.assertIn('<h2>核心指标</h2>', html['content'])
        self.assertIn('<h2>原始依据</h2>', html['content'])
        self.assertIn('<style>', html['content'])
        self.assertIn('@media print', html['content'])
        self.assertIn('class="report-page"', html['content'])
        self.assertIn('class="report-section"', html['content'])
        self.assertEqual('text/html; charset=utf-8', html['content_type'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
