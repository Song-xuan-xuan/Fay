import json
import os
import sqlite3
import time
from collections import Counter
from datetime import datetime, timedelta

from core.dashboard_operational import classify_question_topic


POSITIVE_WORDS = ('谢谢', '好的', '明白', '清楚', '解决', '满意', '不错', '方便')
NEGATIVE_WORDS = ('投诉', '差', '坏', '不行', '没回答', '没听懂', '生气', '退款', '受伤', '危险')
ESCALATION_WORDS = ('人工', '客服', '负责人', '电话', '投诉', '退款', '受伤', '危险')
UNRESOLVED_WORDS = ('没回答', '没听懂', '不是这个', '还是不行', '不知道', '无法确认', '无法处理')
COMPLAINT_WORDS = ('投诉', '差评', '退款', '受伤', '危险', '坏了', '故障')
ACK_WORDS = ('谢谢', '好的', '好', '明白', '清楚', '知道了', '解决了')


def resolve_range(range_key, start_ms=None, end_ms=None):
    end = int(end_ms if end_ms is not None else time.time() * 1000)
    if start_ms is not None:
        return int(start_ms), end
    days = 30 if range_key == '30d' else 1 if range_key == 'today' else 7
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days - 1)
    return int(start_date.timestamp() * 1000), end


def analyze_message(row, reply_text):
    text = row.get('content') or ''
    combined = f"{text}\n{reply_text}"
    sentiment, score = sentiment_label(combined)
    complaint = contains(text, COMPLAINT_WORDS)
    return {
        'msg_id': row['id'], 'session_id': row.get('session_id') or 0,
        'uid': row.get('uid') or 0, 'username': row.get('username') or '',
        'topic': classify_visitor_topic(text, row.get('topic')),
        'sentiment_label': sentiment, 'sentiment_score': score,
        'risk_level': risk_level(text, reply_text, complaint),
        'resolved_status': resolved_status(text, reply_text, complaint),
        'is_complaint': 1 if complaint else 0, 'evidence_text': text,
        'reply_text': reply_text, 'created_at': int(time.time()),
    }


def build_metrics(analyses, tourism):
    count = len(analyses)
    sentiments = Counter(item['sentiment_label'] for item in analyses)
    topics = Counter(item['topic'] for item in analyses)
    risks = Counter(item['risk_level'] for item in analyses)
    unresolved = sum(1 for item in analyses if item['resolved_status'] in ('unresolved', 'escalated'))
    complaints = sum(1 for item in analyses if item['is_complaint'])
    return {
        'message_count': count, 'complaint_count': complaints, 'unresolved_count': unresolved,
        'escalated_count': sum(1 for item in analyses if item['resolved_status'] == 'escalated'),
        'negative_ratio': round(sentiments['negative'] / count, 4) if count else 0,
        'sentiments': dict(sentiments), 'topics': dict(topics), 'risks': dict(risks),
        'top_topics': [{'topic': key, 'count': value} for key, value in topics.most_common(8)],
        'tourism': tourism,
    }


def tourism_context(db_path):
    if not os.path.exists(db_path):
        return {'available': False}
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tourism_visit'").fetchone()
        if not row:
            return {'available': False}
        count, avg_satisfaction = conn.execute('SELECT COUNT(*), AVG(satisfaction) FROM tourism_visit').fetchone()
        return {'available': True, 'record_count': count or 0, 'avg_satisfaction': round(avg_satisfaction or 0, 2)}
    finally:
        conn.close()


def fallback_report_text(metrics):
    topic = metrics['top_topics'][0]['topic'] if metrics['top_topics'] else '暂无明显主题'
    tourism = metrics.get('tourism') or {}
    tourism_text = '暂无游客业务数据补充。'
    if tourism.get('available'):
        tourism_text = f"累计游客数据 {tourism.get('record_count', 0)} 条，平均满意度 {tourism.get('avg_satisfaction', 0)} 分。"
    return (
        f"总体结论：本期共分析 {metrics['message_count']} 条游客消息，主要关注点为 {topic}，"
        f"负面占比 {round(metrics['negative_ratio'] * 100, 1)}%。\n"
        f"游客关注点：投诉 {metrics['complaint_count']} 条，疑似未解决或需人工跟进 "
        f"{metrics['unresolved_count']} 条，升级问题 {metrics['escalated_count']} 条。\n"
        f"游客数据补充：{tourism_text}\n"
        "服务建议：优先补齐高频问题知识库，复核高风险会话，并把重复追问沉淀为标准话术。"
    )


def build_suggestions(metrics, analyses):
    suggestions = []
    if metrics['top_topics']:
        topic = metrics['top_topics'][0]['topic']
        suggestions.append(suggestion('knowledge_base', f'补充{topic}知识库', f'围绕游客高频关注的“{topic}”补充标准问答。'))
    if metrics['complaint_count']:
        suggestions.append(suggestion('manual_followup', '人工跟进投诉会话', '对投诉、退款、安全风险等会话进行人工复核。'))
    if metrics['unresolved_count']:
        suggestions.append(suggestion('script_optimization', '优化未解决问题话术', '为重复追问和兜底回答增加更明确的引导。'))
    if not suggestions and analyses:
        suggestions.append(suggestion('operation_notice', '持续观察游客反馈', '当前未发现明显风险，建议保持周度复盘。'))
    return suggestions


def suggestion(action_type, title, description):
    return {'action_type': action_type, 'title': title, 'description': description, 'status': 'pending'}


def summarize_with_llm(payload):
    from langchain_core.messages import HumanMessage, SystemMessage
    from llm.execution_manager import _get_llm_instance

    llm = _get_llm_instance('big', streaming=False)
    response = llm.invoke([
        SystemMessage(content=(
            '你是景区游客体验分析助手。请输出中文管理报告，必须包含：总体结论、游客关注点分析、'
            '情感趋势与风险、未解决/人工跟进问题、服务优化建议、知识库或话术优化建议。'
            '每部分 1-2 句，避免空泛表述，直接引用输入指标。'
        )),
        HumanMessage(content=json.dumps(payload, ensure_ascii=False)[:6000]),
    ])
    return getattr(response, 'content', '') or ''


def contains(text, words):
    return any(word in str(text or '') for word in words)


def classify_visitor_topic(text, existing_topic=''):
    if contains(text, ('投诉', '坏了', '故障', '客服', '设施', '厕所', '寄存', '轮椅', '母婴')):
        return '服务设施'
    return existing_topic or classify_question_topic(text)


def is_ack_only(text):
    normalized = str(text or '').strip().replace('，', '').replace('。', '').replace('！', '').replace('!', '')
    return 0 < len(normalized) <= 8 and any(word == normalized or word in normalized for word in ACK_WORDS)


def sentiment_label(text):
    positive = sum(1 for word in POSITIVE_WORDS if word in text)
    negative = sum(1 for word in NEGATIVE_WORDS if word in text)
    if negative > positive:
        return 'negative', round(-0.4 - min(negative, 3) * 0.2, 2)
    if positive > negative:
        return 'positive', round(0.4 + min(positive, 3) * 0.2, 2)
    return 'neutral', 0.0


def risk_level(text, reply_text, complaint):
    combined = f"{text}\n{reply_text}"
    if complaint or contains(combined, ESCALATION_WORDS):
        return 'high'
    if contains(combined, UNRESOLVED_WORDS):
        return 'medium'
    return 'low'


def resolved_status(text, reply_text, complaint):
    combined = f"{text}\n{reply_text}"
    if complaint or contains(combined, ESCALATION_WORDS):
        return 'escalated'
    if contains(combined, UNRESOLVED_WORDS):
        return 'unresolved'
    if contains(combined, POSITIVE_WORDS):
        return 'resolved'
    return 'unknown'
