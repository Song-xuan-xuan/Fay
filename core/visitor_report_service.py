import os
import sqlite3
from collections import defaultdict
from dataclasses import dataclass

from core.visitor_report_rules import (
    analyze_message,
    build_metrics,
    build_suggestions,
    fallback_report_text,
    is_ack_only,
    resolve_range,
    summarize_with_llm,
    tourism_context,
)
from core.visitor_report_storage import (
    ACTION_STATUS,
    create_schema,
    fetch_actions,
    insert_actions,
    insert_analyses,
    insert_report,
    markdown_to_html,
    report_row,
    report_to_markdown,
)


EXPORT_EVIDENCE_LIMIT = 20


@dataclass(frozen=True)
class VisitorReportPaths:
    fay_db_path: str = os.path.join('memory', 'fay.db')
    user_db_path: str = os.path.join('memory', 'user_profiles.db')
    tourism_db_path: str = os.path.join('memory', 'tourism.db')
    report_db_path: str = os.path.join('memory', 'visitor_reports.db')


class VisitorReportService:
    def __init__(self, paths=None, llm_summarizer=None):
        self.paths = paths or VisitorReportPaths()
        self.llm_summarizer = llm_summarizer or summarize_with_llm

    def ensure_schema(self):
        os.makedirs(os.path.dirname(self.paths.report_db_path), exist_ok=True)
        conn = sqlite3.connect(self.paths.report_db_path)
        try:
            create_schema(conn)
            conn.commit()
        finally:
            conn.close()

    def analyze_interactions(self, range_key='7d', start_ms=None, end_ms=None):
        start, end = resolve_range(range_key, start_ms, end_ms)
        admin_users, admin_uids = _load_admin_identity(self.paths.user_db_path)
        rows = _fetch_messages(self.paths.fay_db_path, start, end)
        reply_lookup = _build_reply_lookup(rows)
        analyses = []
        for row in rows:
            if row['type'] == 'fay' or _is_admin(row, admin_users, admin_uids):
                continue
            if is_ack_only(row.get('content')):
                continue
            analyses.append(analyze_message(row, reply_lookup.get(row['id'], '')))
        return analyses

    def generate_report(self, range_key='7d', start_ms=None, end_ms=None, created_by='system'):
        self.ensure_schema()
        start, end = resolve_range(range_key, start_ms, end_ms)
        analyses = self.analyze_interactions(range_key, start, end)
        metrics = build_metrics(analyses, tourism_context(self.paths.tourism_db_path))
        report_text = self._build_report_text(metrics, analyses, range_key)
        suggestions = build_suggestions(metrics, analyses)
        conn = sqlite3.connect(self.paths.report_db_path)
        try:
            report_id = insert_report(conn, range_key, start, end, metrics, report_text, suggestions, created_by)
            insert_analyses(conn, report_id, analyses)
            actions = insert_actions(conn, report_id, suggestions)
            conn.commit()
            return self.get_report(report_id, actions=actions)
        finally:
            conn.close()

    def latest_report(self):
        self.ensure_schema()
        rows = self.list_reports(limit=1)
        return rows[0] if rows else None

    def list_reports(self, limit=20):
        self.ensure_schema()
        conn = _connect_rows(self.paths.report_db_path)
        try:
            rows = conn.execute(
                '''SELECT * FROM visitor_experience_report
                ORDER BY created_at DESC, id DESC LIMIT ?''',
                (int(limit),),
            ).fetchall()
            return [report_row(row) for row in rows]
        finally:
            conn.close()

    def get_report(self, report_id, actions=None):
        self.ensure_schema()
        conn = _connect_rows(self.paths.report_db_path)
        try:
            row = conn.execute('SELECT * FROM visitor_experience_report WHERE id = ?', (int(report_id),)).fetchone()
            if not row:
                return None
            report = report_row(row)
            report['actions'] = actions if actions is not None else fetch_actions(conn, report['id'])
            return report
        finally:
            conn.close()

    def get_evidence(self, report_id, limit=50):
        self.ensure_schema()
        conn = _connect_rows(self.paths.report_db_path)
        try:
            rows = conn.execute(
                '''SELECT * FROM visitor_interaction_analysis
                WHERE report_id = ? ORDER BY risk_level DESC, id ASC LIMIT ?''',
                (int(report_id), int(limit)),
            ).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def update_action_status(self, action_id, status):
        if status not in ACTION_STATUS:
            raise ValueError('invalid action status')
        self.ensure_schema()
        conn = _connect_rows(self.paths.report_db_path)
        try:
            conn.execute('UPDATE visitor_report_action SET status = ? WHERE id = ?', (status, int(action_id)))
            conn.commit()
            row = conn.execute('SELECT * FROM visitor_report_action WHERE id = ?', (int(action_id),)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def export_report(self, report_id, fmt='md'):
        report = self.get_report(report_id)
        if not report:
            return None
        report['evidence'] = self.get_evidence(report_id, limit=EXPORT_EVIDENCE_LIMIT)
        markdown = report_to_markdown(report)
        if fmt == 'html':
            return _export_payload(report_id, 'html', 'text/html; charset=utf-8', markdown_to_html(markdown))
        return _export_payload(report_id, 'md', 'text/markdown; charset=utf-8', markdown)

    def _build_report_text(self, metrics, analyses, range_key):
        payload = {'metrics': metrics, 'analyses': analyses[:20], 'range': range_key}
        try:
            text = self.llm_summarizer(payload)
        except Exception:
            text = ''
        return text.strip() if text and text.strip() else fallback_report_text(metrics)


def _connect_rows(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _export_payload(report_id, ext, content_type, content):
    return {
        'filename': f"visitor-report-{report_id}.{ext}",
        'content_type': content_type,
        'content': content,
    }


def _load_admin_identity(db_path):
    if not os.path.exists(db_path):
        return set(), set()
    conn = sqlite3.connect(db_path)
    try:
        columns = {row[1] for row in conn.execute('PRAGMA table_info(T_Member)').fetchall()}
        if not columns or 'role' not in columns:
            return set(), set()
        rows = conn.execute("SELECT username, id FROM T_Member WHERE role = 'admin'").fetchall()
        return {row[0] for row in rows if row[0]}, {int(row[1]) for row in rows if row[1] is not None}
    finally:
        conn.close()


def _fetch_messages(db_path, start_ms, end_ms):
    if not os.path.exists(db_path):
        return []
    conn = _connect_rows(db_path)
    try:
        rows = conn.execute(
            '''SELECT id, type, content, createtime, username, COALESCE(uid, 0) AS uid,
               COALESCE(session_id, 0) AS session_id, COALESCE(topic, '') AS topic
            FROM T_Msg WHERE createtime BETWEEN ? AND ? ORDER BY session_id, id''',
            (int(start_ms), int(end_ms)),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def _build_reply_lookup(rows):
    lookup = {}
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row.get('session_id') or 0, row.get('username') or '')].append(row)
    for group_rows in grouped.values():
        _add_group_replies(lookup, group_rows)
    return lookup


def _add_group_replies(lookup, group_rows):
    for index, row in enumerate(group_rows):
        if row['type'] == 'fay':
            continue
        replies = []
        for next_row in group_rows[index + 1:]:
            if next_row['type'] != 'fay' and is_ack_only(next_row.get('content')):
                replies.append(next_row['content'])
                break
            if next_row['type'] != 'fay':
                break
            replies.append(next_row['content'])
        lookup[row['id']] = '\n'.join(replies)


def _is_admin(row, admin_users, admin_uids):
    return row.get('username') in admin_users or int(row.get('uid') or 0) in admin_uids
