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

    def get_overview(self, range_key='7d', is_admin=False):
        self.import_tourism_excel(force=False)
        operations = operational_summary(self.paths.fay_db_path, range_key)
        users = user_metrics(self.paths.user_db_path, is_admin=is_admin)
        tourism = self.get_tourism({})
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
                'source': latest_source(self.paths.tourism_db_path),
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
        context = payload or {}
        overview = context.get('overview') or {}
        kpis = overview.get('kpis') or []
        if not kpis:
            overview = self.get_overview()
            kpis = overview.get('kpis') or []
        lookup = {item.get('title'): item.get('value') for item in kpis}
        return {
            'text': (
                f"今日服务人次 {lookup.get('今日服务人次', 0)}，本周服务人次 {lookup.get('本周服务人次', 0)}。"
                f"当前低满意预警为 {lookup.get('低满意预警', 0)} 条，建议优先关注门票开放、交通路线和服务设施类问题，"
                "并结合景区排行与满意度趋势调整数字人问答话术。"
            )
        }


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
