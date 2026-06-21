import os
import sqlite3
from dataclasses import dataclass

from core.dashboard_operational import (
    classify_question_topic,
    hot_topics,
    mask_email,
    operational_summary,
    service_trends,
    user_metrics,
)
from core.dashboard_tourism import import_tourism_excel, latest_source, normalize_excel_text


LOW_SATISFACTION_MAX = 2
DASHBOARD_ATTRACTIONS = ('灵山胜境', '禅意小镇·拈花湾')
DEFAULT_DASHBOARD_ATTRACTION = DASHBOARD_ATTRACTIONS[0]
TOURISM_FILTER_KEYS = (
    'start_date',
    'end_date',
    'attraction_type',
    'attraction_name',
    'satisfaction_min',
    'satisfaction_max',
    'tourist_segment',
)


@dataclass(frozen=True)
class DashboardPaths:
    project_root: str = os.getcwd()
    fay_db_path: str = os.path.join('memory', 'fay.db')
    user_db_path: str = os.path.join('memory', 'user_profiles.db')
    tourism_db_path: str = os.path.join('memory', 'tourism.db')
    tourism_excel_path: str = os.path.join('data', '景点景区旅游数据行为分析数据.xlsx')


def repair_text(value):
    return normalize_excel_text(value)


class DashboardService:
    def __init__(self, paths=None):
        self.paths = paths or self.default_paths()

    @classmethod
    def default_paths(cls):
        root = os.getcwd()
        return DashboardPaths(
            project_root=root,
            fay_db_path=os.path.join(root, 'memory', 'fay.db'),
            user_db_path=os.path.join(root, 'memory', 'user_profiles.db'),
            tourism_db_path=os.path.join(root, 'memory', 'tourism.db'),
            tourism_excel_path=_find_tourism_excel(root),
        )

    def import_tourism_excel(self, force=False):
        return import_tourism_excel(self.paths.tourism_db_path, self.paths.tourism_excel_path, force=force)

    def get_overview(self, range_key='7d', is_admin=False, tourism_filters=None):
        self.import_tourism_excel(force=False)
        operations = operational_summary(self.paths.fay_db_path, range_key)
        users = user_metrics(self.paths.user_db_path, is_admin=is_admin)
        tourism = self.get_tourism(tourism_filters or {})
        average_satisfaction = tourism.get('average_satisfaction', 0)
        kpis = [
            _kpi('今日服务人次', operations['today_services'], '人次', '系统运行数据'),
            _kpi('本周服务人次', operations['week_services'], '人次', '系统运行数据'),
            _kpi('今日问答次数', operations['today_questions'], '次', '系统运行数据'),
            _kpi('今日新增注册', users['today_new_users'], '人', '用户管理模块'),
            _kpi('累计注册用户', users['total_users'], '人', '用户管理模块'),
            _kpi('本周活跃用户', users['week_active_users'], '人', '用户管理模块'),
            _kpi('游客平均满意度', round(average_satisfaction, 2), '分', '旅游 Excel'),
            _kpi('低满意预警', tourism.get('low_satisfaction_count', 0), '条', '旅游 Excel'),
        ]
        return {
            'is_demo': False,
            'data_source': 'system_sqlite_and_excel',
            'kpis': kpis,
            'operations': operations,
            'users': users,
            'tourism_source': tourism.get('source', {}),
        }

    def get_service_trends(self, range_key='7d'):
        return {'range': range_key, 'items': service_trends(self.paths.fay_db_path, range_key)}

    def get_hot_topics(self, range_key='7d'):
        return {'range': range_key, 'items': hot_topics(self.paths.fay_db_path, range_key)}

    def get_user_metrics(self, is_admin=False):
        return user_metrics(self.paths.user_db_path, is_admin=is_admin)

    def get_tourism(self, filters):
        self.import_tourism_excel(force=False)
        where, params = _build_tourism_where(filters or {})
        conn = sqlite3.connect(self.paths.tourism_db_path)
        try:
            return {
                'source': _filtered_source(conn, self.paths.tourism_db_path, where, params, filters or {}),
                'type_metrics': _query_type_metrics(conn, where, params),
                'attraction_ranking': _query_attraction_ranking(conn, where, params),
                'satisfaction_trend': _query_satisfaction_trend(conn, where, params),
                'visit_trend': _query_visit_trend(conn, where, params),
                'satisfaction_distribution': _query_satisfaction_distribution(conn, where, params),
                'consumption_structure': _query_consumption(conn, where, params),
                'tourist_profile': _query_tourist_profile(conn, where, params),
                'details': _query_details(conn, where, params),
                'average_satisfaction': _scalar(conn, f'SELECT AVG(satisfaction) FROM tourism_visit {where}', params),
                'low_satisfaction_count': int(_scalar(conn, f'SELECT COUNT(*) FROM tourism_visit {where} AND satisfaction <= ?', [*params, LOW_SATISFACTION_MAX])),
            }
        finally:
            conn.close()

    def explain(self, payload):
        context = payload if isinstance(payload, dict) else {}
        scope = _explain_scope(context.get('scope'))
        fallback_filters = _tourism_filters_from_context(context)
        overview = context.get('overview') if isinstance(context.get('overview'), dict) else {}
        if not overview.get('kpis'):
            overview = self.get_overview(context.get('range') or '7d', tourism_filters=fallback_filters)
        topics = context.get('topics') if isinstance(context.get('topics'), list) else []
        tourism = context.get('tourism') if isinstance(context.get('tourism'), dict) else {}
        if scope == 'tourism' and not _has_tourism_snapshot(tourism):
            tourism = self.get_tourism(fallback_filters)
        if scope == 'tourism':
            return _tourism_explanation(context, overview, topics, tourism)
        return _overview_explanation(context, overview, topics, tourism)


def _explain_scope(value):
    return 'tourism' if str(value or '').strip().lower() == 'tourism' else 'overview'


def _tourism_filters_from_context(context):
    filters = context.get('filters') if isinstance(context.get('filters'), dict) else {}
    result = {key: filters.get(key) for key in TOURISM_FILTER_KEYS if filters.get(key) not in (None, '')}
    for key in TOURISM_FILTER_KEYS:
        value = context.get(key)
        if value not in (None, ''):
            result[key] = value
    return result


def _overview_explanation(context, overview, topics, tourism):
    lookup = _kpi_lookup(overview)
    topic = _top_topic(topics)
    range_text = _range_text(context.get('range'))
    topic_text = _topic_sentence(topic)
    low = _value_text(lookup.get('低满意预警'))
    avg = _value_text(lookup.get('游客平均满意度'))
    text = (
        f"当前统计范围为{range_text}。今日服务人次 {_value_text(lookup.get('今日服务人次'))}，"
        f"本周服务人次 {_value_text(lookup.get('本周服务人次'))}，今日问答次数 {_value_text(lookup.get('今日问答次数'))}。"
        f"用户侧本周活跃 {_value_text(lookup.get('本周活跃用户'))} 人，游客平均满意度 {avg} 分，"
        f"低满意预警 {low} 条。{topic_text}"
        "运营上建议先复盘低满意会话，再把高频问题沉淀到知识库和数字人标准话术中。"
    )
    return {
        'scope': 'overview',
        'title': '大盘运营解读',
        'text': text,
        'highlights': [
            f"本周服务人次 {_value_text(lookup.get('本周服务人次'))}",
            f"低满意预警 {low} 条",
            _highlight_topic(topic),
        ],
        'actions': _overview_actions(topic),
    }


def _tourism_explanation(context, overview, topics, tourism):
    lookup = _kpi_lookup(overview)
    top = _top_attraction(tourism)
    top_type = _top_type(tourism)
    trend = _latest_satisfaction(tourism)
    topic = _top_topic(topics)
    avg = _value_text(_first_present(tourism.get('average_satisfaction'), lookup.get('游客平均满意度')))
    low = _value_text(_first_present(tourism.get('low_satisfaction_count'), lookup.get('低满意预警')))
    record_count = _record_count(tourism)
    text = (
        f"景区数据当前累计 {record_count} 条记录，平均满意度 {avg} 分，低满意预警 {low} 条。"
        f"{_top_attraction_sentence(top)}{_top_type_sentence(top_type)}{_trend_sentence(trend)}"
        f"{_topic_sentence(topic)}"
        "建议围绕访问量最高和低满意风险最高的场景，优先优化数字人对交通、门票、排队和服务设施的回答。"
    )
    return {
        'scope': 'tourism',
        'title': '景区数据解读',
        'text': text,
        'highlights': [
            f"旅游记录 {record_count} 条",
            f"平均满意度 {avg} 分",
            _highlight_attraction(top),
        ],
        'actions': _tourism_actions(top, top_type),
    }


def _kpi_lookup(overview):
    kpis = overview.get('kpis') if isinstance(overview, dict) else []
    return {
        item.get('title'): item.get('value')
        for item in kpis
        if isinstance(item, dict) and item.get('title')
    }


def _value_text(value, default='0'):
    if value in (None, ''):
        return default
    if isinstance(value, float):
        return str(round(value, 2)).rstrip('0').rstrip('.')
    return str(value)


def _first_present(*values):
    for value in values:
        if value not in (None, ''):
            return value
    return None


def _range_text(value):
    return {'7d': '最近 7 天', '30d': '最近 30 天', 'week': '本周', 'month': '本月'}.get(value, '当前筛选条件')


def _top_topic(topics):
    items = [item for item in topics if isinstance(item, dict)]
    if not items:
        return {}
    return max(items, key=lambda item: _to_number(item.get('count')))


def _topic_sentence(topic):
    if not topic:
        return "当前暂未形成明显高频问答主题。"
    question = topic.get('representative_question') or '暂无代表问题'
    return f"问答热点集中在“{topic.get('topic', '未分类')}”，出现 {_value_text(topic.get('count'))} 次，代表问题是“{question}”。"


def _highlight_topic(topic):
    if not topic:
        return "暂无明显问答热点"
    return f"热点主题 {topic.get('topic', '未分类')} {_value_text(topic.get('count'))} 次"


def _overview_actions(topic):
    focus = topic.get('topic') if topic else '热门问答'
    return [
        f"将“{focus}”相关问题补充到知识库和数字人标准话术。",
        "复盘低满意预警会话，标记是否属于门票、交通或设施类问题。",
        "结合服务趋势安排高峰时段值守，异常上涨时检查 ASR、TTS 和接口状态。",
    ]


def _has_tourism_snapshot(tourism):
    keys = ('attraction_ranking', 'type_metrics', 'satisfaction_trend', 'visit_trend')
    return any(isinstance(tourism.get(key), list) and tourism.get(key) for key in keys)


def _top_attraction(tourism):
    items = tourism.get('attraction_ranking') if isinstance(tourism, dict) else []
    items = [item for item in (items or []) if isinstance(item, dict)]
    if not items:
        return {}
    return max(items, key=lambda item: _to_number(item.get('visits')))


def _top_type(tourism):
    items = tourism.get('type_metrics') if isinstance(tourism, dict) else []
    items = [item for item in (items or []) if isinstance(item, dict)]
    if not items:
        return {}
    return max(items, key=lambda item: _to_number(item.get('visits')))


def _latest_satisfaction(tourism):
    items = tourism.get('satisfaction_trend') if isinstance(tourism, dict) else []
    items = [item for item in (items or []) if isinstance(item, dict)]
    return items[-1] if items else {}


def _record_count(tourism):
    source = tourism.get('source') if isinstance(tourism.get('source'), dict) else {}
    return _value_text(_first_present(source.get('record_count'), source.get('row_count')))


def _top_attraction_sentence(top):
    if not top:
        return "当前景点排行数据不足。"
    return (
        f"访问最高的是“{top.get('attraction_name', '未命名景点')}”，类型为{top.get('attraction_type', '未分类')}，"
        f"访问 {_value_text(top.get('visits'))} 次，平均满意度 {_value_text(top.get('avg_satisfaction'))} 分。"
    )


def _top_type_sentence(top_type):
    if not top_type:
        return ""
    return f"景区类型中“{top_type.get('name', '未分类')}”访问量靠前，共 {_value_text(top_type.get('visits'))} 次。"


def _trend_sentence(trend):
    if not trend:
        return ""
    low_ratio = round(_to_number(trend.get('low_ratio')) * 100, 1)
    return f"最新满意度趋势为 {trend.get('month', '最近一期')} 平均 {_value_text(trend.get('avg_satisfaction'))} 分，低满意占比 {low_ratio}%。"


def _highlight_attraction(top):
    if not top:
        return "暂无景点排行"
    return f"访问最高 {top.get('attraction_name', '未命名景点')} {_value_text(top.get('visits'))} 次"


def _tourism_actions(top, top_type):
    attraction = top.get('attraction_name') if top else '重点景区'
    type_name = top_type.get('name') if top_type else '高访问类型'
    return [
        f"为“{attraction}”补充开放时间、排队、交通和消费提示话术。",
        f"针对“{type_name}”整理 3-5 个高频问题，更新知识库索引。",
        "抽查低满意样本，区分服务态度、设施、价格和路线问题后分派处理。",
    ]


def _to_number(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0


def _find_tourism_excel(root):
    candidates = [
        os.path.join(root, 'data', 'imports', 'tourism_behavior.xlsx'),
        os.path.join(root, 'data', '景点景区旅游数据行为分析数据.xlsx'),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[-1]


def _kpi(title, value, unit, source):
    return {'title': title, 'value': value, 'unit': unit, 'source': source, 'is_demo': False, 'change': 0}


def _build_tourism_where(filters):
    clauses = ['1=1']
    params = []
    mapping = {
        'start_date': ('visit_date >= ?', str),
        'end_date': ('visit_date <= ?', str),
        'attraction_type': ('attraction_type = ?', str),
        'attraction_name': ('attraction_name LIKE ?', lambda value: f'%{value}%'),
        'satisfaction_min': ('satisfaction >= ?', int),
        'satisfaction_max': ('satisfaction <= ?', int),
        'tourist_segment': (_age_segment_expr() + ' = ?', str),
    }
    for key, (clause, converter) in mapping.items():
        value = filters.get(key)
        if value in (None, ''):
            continue
        clauses.append(clause)
        params.append(converter(value))
    return 'WHERE ' + ' AND '.join(clauses), params


def _filtered_source(conn, db_path, where, params, filters):
    source = latest_source(db_path) or {}
    row = conn.execute(f'SELECT COUNT(*), MIN(visit_date), MAX(visit_date) FROM tourism_visit {where}', params).fetchone()
    record_count = int(row[0] or 0) if row else 0
    result = dict(source)
    total = result.get('row_count') or result.get('record_count') or 0
    result['total_record_count'] = total
    result['record_count'] = record_count
    result['date_range'] = {'start': (row[1] if row else '') or '', 'end': (row[2] if row else '') or ''}
    selected = filters.get('attraction_name') if isinstance(filters, dict) else ''
    if selected:
        result['selected_attraction'] = str(selected)
    return result


def _age_segment_expr():
    return '''CASE
        WHEN age < 18 THEN '18岁以下'
        WHEN age < 30 THEN '18-29岁'
        WHEN age < 45 THEN '30-44岁'
        WHEN age < 60 THEN '45-59岁'
        ELSE '60岁以上' END'''


def _query_type_metrics(conn, where, params):
    rows = conn.execute(
        f'''SELECT attraction_type, COUNT(*), COUNT(DISTINCT tourist_id), AVG(satisfaction), AVG(total_cost)
        FROM tourism_visit {where}
        GROUP BY attraction_type ORDER BY COUNT(*) DESC LIMIT 8''',
        params,
    ).fetchall()
    return [
        {'name': row[0] or '未分类', 'visits': row[1], 'tourists': row[2], 'avg_satisfaction': round(row[3] or 0, 2), 'avg_cost': round(row[4] or 0, 2)}
        for row in rows
    ]


def _query_attraction_ranking(conn, where, params):
    rows = conn.execute(
        f'''SELECT attraction_name, attraction_type, COUNT(*), AVG(satisfaction), AVG(total_cost)
        FROM tourism_visit {where}
        GROUP BY attraction_name, attraction_type ORDER BY COUNT(*) DESC LIMIT 10''',
        params,
    ).fetchall()
    return [
        {'attraction_name': row[0], 'attraction_type': row[1], 'visits': row[2], 'avg_satisfaction': round(row[3] or 0, 2), 'avg_cost': round(row[4] or 0, 2)}
        for row in rows
    ]


def _query_satisfaction_trend(conn, where, params):
    rows = conn.execute(
        f'''SELECT substr(visit_date, 1, 7), AVG(satisfaction),
        SUM(CASE WHEN satisfaction <= ? THEN 1 ELSE 0 END) * 1.0 / COUNT(*)
        FROM tourism_visit {where}
        GROUP BY substr(visit_date, 1, 7) ORDER BY substr(visit_date, 1, 7) ASC''',
        [LOW_SATISFACTION_MAX, *params],
    ).fetchall()
    return [{'month': row[0], 'avg_satisfaction': round(row[1] or 0, 2), 'low_ratio': round(row[2] or 0, 4)} for row in rows]


def _query_visit_trend(conn, where, params):
    rows = conn.execute(
        f'''SELECT substr(visit_date, 1, 7), COUNT(*), COUNT(DISTINCT tourist_id)
        FROM tourism_visit {where}
        GROUP BY substr(visit_date, 1, 7) ORDER BY substr(visit_date, 1, 7) ASC''',
        params,
    ).fetchall()
    return [{'month': row[0], 'visits': row[1], 'tourists': row[2]} for row in rows]


def _query_satisfaction_distribution(conn, where, params):
    rows = conn.execute(
        f'''SELECT CASE
            WHEN satisfaction <= 2 THEN '低满意'
            WHEN satisfaction = 3 THEN '中性'
            ELSE '高满意' END AS level, COUNT(*)
        FROM tourism_visit {where} GROUP BY level''',
        params,
    ).fetchall()
    counts = {row[0]: row[1] for row in rows}
    return [{'name': name, 'count': counts.get(name, 0)} for name in ('低满意', '中性', '高满意')]


def _query_consumption(conn, where, params):
    row = conn.execute(
        f'''SELECT AVG(ticket_cost), AVG(food_cost), AVG(shopping_cost), AVG(transport_cost), AVG(entertainment_cost), AVG(total_cost)
        FROM tourism_visit {where}''',
        params,
    ).fetchone() or (0, 0, 0, 0, 0, 0)
    labels = ['门票', '餐饮', '购物', '交通', '娱乐']
    return {
        'avg_total_cost': round(row[5] or 0, 2),
        'items': [{'name': labels[index], 'value': round(row[index] or 0, 2)} for index in range(5)],
    }


def _query_tourist_profile(conn, where, params):
    segment_expr = _age_segment_expr()
    age_rows = conn.execute(
        f'''SELECT {segment_expr} AS age_group, COUNT(*)
        FROM tourism_visit {where} GROUP BY age_group ORDER BY COUNT(*) DESC''',
        params,
    ).fetchall()
    gender_rows = conn.execute(f'SELECT gender, COUNT(*) FROM tourism_visit {where} GROUP BY gender', params).fetchall()
    return {
        'age_groups': [{'name': row[0], 'count': row[1]} for row in age_rows],
        'gender_distribution': [{'name': row[0] or '未知', 'count': row[1]} for row in gender_rows],
    }


def _query_details(conn, where, params):
    segment_expr = _age_segment_expr()
    rows = conn.execute(
        f'''SELECT visit_date, tourist_id, attraction_name, attraction_type, total_cost, satisfaction,
        {segment_expr} AS tourist_segment
        FROM tourism_visit {where} ORDER BY visit_date DESC, id DESC LIMIT 20''',
        params,
    ).fetchall()
    return [
        {
            'visit_date': row[0], 'tourist_id': row[1], 'attraction_name': row[2],
            'attraction_type': row[3], 'total_cost': row[4], 'satisfaction': row[5],
            'tourist_segment': row[6],
        }
        for row in rows
    ]


def _scalar(conn, sql, params):
    row = conn.execute(sql, params).fetchone()
    return row[0] if row and row[0] is not None else 0
