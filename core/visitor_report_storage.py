import json
import sqlite3
import time
from datetime import datetime

from core.visitor_report_html import render_report_html


ACTION_STATUS = {'pending', 'processing', 'done', 'ignored'}
STATUS_LABELS = {'pending': '待处理', 'processing': '处理中', 'done': '已完成', 'ignored': '已忽略'}
SENTIMENT_LABELS = {'positive': '正向', 'neutral': '中性', 'negative': '负向'}
RISK_LABELS = {'high': '高', 'medium': '中', 'low': '低'}
RESOLVED_LABELS = {'resolved': '已解决', 'unresolved': '未解决', 'escalated': '已升级', 'unknown': '未知'}


def create_schema(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS visitor_experience_report (
        id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, report_type TEXT,
        range_key TEXT, range_start INTEGER, range_end INTEGER, status TEXT,
        metrics_json TEXT, report_text TEXT, suggestions_json TEXT,
        created_by TEXT, created_at INTEGER)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS visitor_interaction_analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT, report_id INTEGER, msg_id INTEGER,
        session_id INTEGER, uid INTEGER, username TEXT, topic TEXT,
        sentiment_label TEXT, sentiment_score REAL, risk_level TEXT,
        resolved_status TEXT, is_complaint INTEGER, evidence_text TEXT,
        reply_text TEXT, created_at INTEGER)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS visitor_report_action (
        id INTEGER PRIMARY KEY AUTOINCREMENT, report_id INTEGER, action_type TEXT,
        title TEXT, description TEXT, status TEXT, created_at INTEGER)''')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_visitor_report_created ON visitor_experience_report(created_at)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_visitor_analysis_report ON visitor_interaction_analysis(report_id)')


def insert_report(conn, range_key, start, end, metrics, text, suggestions, created_by):
    now = int(time.time())
    title = f"游客感受度报告 {datetime.fromtimestamp(now).strftime('%Y-%m-%d %H:%M')}"
    conn.execute(
        '''INSERT INTO visitor_experience_report
        (title, report_type, range_key, range_start, range_end, status, metrics_json,
         report_text, suggestions_json, created_by, created_at)
        VALUES (?, 'manual', ?, ?, ?, 'success', ?, ?, ?, ?, ?)''',
        (title, range_key, start, end, json.dumps(metrics, ensure_ascii=False),
         text, json.dumps(suggestions, ensure_ascii=False), created_by, now),
    )
    return conn.execute('SELECT last_insert_rowid()').fetchone()[0]


def insert_analyses(conn, report_id, analyses):
    rows = [(
        report_id, item['msg_id'], item['session_id'], item['uid'], item['username'], item['topic'],
        item['sentiment_label'], item['sentiment_score'], item['risk_level'], item['resolved_status'],
        item['is_complaint'], item['evidence_text'], item['reply_text'], item['created_at'],
    ) for item in analyses]
    conn.executemany(
        '''INSERT INTO visitor_interaction_analysis
        (report_id, msg_id, session_id, uid, username, topic, sentiment_label, sentiment_score,
         risk_level, resolved_status, is_complaint, evidence_text, reply_text, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        rows,
    )


def insert_actions(conn, report_id, suggestions):
    now = int(time.time())
    rows = [(report_id, item['action_type'], item['title'], item['description'], item['status'], now) for item in suggestions]
    conn.executemany(
        '''INSERT INTO visitor_report_action
        (report_id, action_type, title, description, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?)''',
        rows,
    )
    return fetch_actions(conn, report_id)


def fetch_actions(conn, report_id):
    rows = conn.execute('SELECT * FROM visitor_report_action WHERE report_id = ? ORDER BY id ASC', (int(report_id),)).fetchall()
    return [dict(row) if isinstance(row, sqlite3.Row) else action_tuple(row) for row in rows]


def action_tuple(row):
    keys = ('id', 'report_id', 'action_type', 'title', 'description', 'status', 'created_at')
    return dict(zip(keys, row))


def report_row(row):
    data = dict(row)
    data['metrics'] = json.loads(data.pop('metrics_json') or '{}')
    data['suggestions'] = json.loads(data.pop('suggestions_json') or '[]')
    return data


def report_to_markdown(report):
    lines = ['# 游客感受度报告']
    _append_report_summary(lines, report.get('report_text', ''))
    lines.extend(_core_metric_lines(report.get('metrics') or {}))
    lines.extend(_topic_lines(report.get('metrics') or {}))
    lines.extend(_sentiment_risk_lines(report.get('metrics') or {}))
    lines.extend(_tourism_lines(report.get('metrics') or {}))
    lines.extend(_evidence_lines(report.get('evidence') or []))
    lines.extend(_action_lines(report.get('actions') or report.get('suggestions') or []))
    return '\n'.join(lines).strip() + '\n'


def markdown_to_html(markdown):
    return render_report_html(markdown)


def _append_report_summary(lines, text):
    if not str(text or '').strip():
        return
    lines.extend(['', '## 报告摘要'])
    for paragraph in str(text).strip().splitlines():
        if paragraph.strip():
            lines.append(paragraph.strip())


def _core_metric_lines(metrics):
    return [
        '', '## 核心指标',
        f"- 消息量：{_number(metrics.get('message_count'))}",
        f"- 投诉量：{_number(metrics.get('complaint_count'))}",
        f"- 未解决/需跟进：{_number(metrics.get('unresolved_count'))}",
        f"- 升级问题：{_number(metrics.get('escalated_count'))}",
        f"- 负面占比：{_percent(metrics.get('negative_ratio'))}",
    ]


def _topic_lines(metrics):
    lines = ['', '## 关注点分析']
    topics = metrics.get('top_topics') or _topic_items(metrics.get('topics') or {})
    if not topics:
        return lines + ['暂无明显高频关注点。']
    for item in topics:
        lines.append(f"- {item.get('topic') or '未分类'}：{_number(item.get('count'))} 条")
    return lines


def _sentiment_risk_lines(metrics):
    lines = ['', '## 情感与风险']
    lines.append(f"- 情感分布：{_count_summary(metrics.get('sentiments') or {}, SENTIMENT_LABELS)}")
    lines.append(f"- 风险分布：{_count_summary(metrics.get('risks') or {}, RISK_LABELS)}")
    risk_text = _risk_summary(metrics)
    if risk_text:
        lines.append(f"- 风险提示：{risk_text}")
    return lines


def _tourism_lines(metrics):
    tourism = metrics.get('tourism') or {}
    if not tourism.get('available'):
        return []
    return [
        '', '## 游客数据补充',
        f"- 累计记录数：{_number(tourism.get('record_count'))}",
        f"- 平均满意度：{_number(tourism.get('avg_satisfaction'))}",
    ]


def _evidence_lines(evidence):
    lines = ['', '## 原始依据']
    if not evidence:
        return lines + ['暂无可导出的原始依据。']
    for item in evidence[:20]:
        header = _evidence_header(item)
        text = str(item.get('evidence_text') or '').strip()
        reply = str(item.get('reply_text') or '').strip()
        lines.append(f"- {header}：{text or '无游客原文'}")
        if reply:
            lines.append(f"  回复：{reply}")
    return lines


def _action_lines(actions):
    lines = ['', '## 服务建议']
    if not actions:
        return lines + ['暂无待办建议。']
    for action in actions:
        status = STATUS_LABELS.get(action.get('status'), action.get('status', '待处理'))
        lines.append(f"- [{status}] {action.get('title')}: {action.get('description')}")
    return lines


def _topic_items(topics):
    return [{'topic': key, 'count': value} for key, value in sorted(topics.items(), key=lambda item: item[1], reverse=True)]


def _count_summary(source, labels):
    if not source:
        return '暂无数据'
    parts = [f"{labels.get(key, key)} {_number(value)}" for key, value in source.items()]
    return '，'.join(parts)


def _risk_summary(metrics):
    complaints = _number(metrics.get('complaint_count'))
    unresolved = _number(metrics.get('unresolved_count'))
    escalated = _number(metrics.get('escalated_count'))
    if complaints or unresolved or escalated:
        return f"投诉 {complaints} 条，未解决/需跟进 {unresolved} 条，升级 {escalated} 条。"
    return '未识别明显投诉、升级或未解决风险。'


def _evidence_header(item):
    topic = item.get('topic') or '未分类'
    sentiment = SENTIMENT_LABELS.get(item.get('sentiment_label'), item.get('sentiment_label') or '未知')
    risk = RISK_LABELS.get(item.get('risk_level'), item.get('risk_level') or '未知')
    resolved = RESOLVED_LABELS.get(item.get('resolved_status'), item.get('resolved_status') or '未知')
    return f"{topic} / {sentiment} / 风险{risk} / {resolved}"


def _percent(value):
    return f"{round(float(value or 0) * 100, 1)}%"


def _number(value):
    return int(value or 0) if isinstance(value, int) or float(value or 0).is_integer() else round(float(value), 2)
