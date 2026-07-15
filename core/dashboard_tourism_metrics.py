import sqlite3

from core.dashboard_tourism import latest_source_from_connection


LOW_SATISFACTION_MAX = 2
TOURISM_FILTER_KEYS = (
    'start_date',
    'end_date',
    'attraction_type',
    'attraction_name',
    'satisfaction_min',
    'satisfaction_max',
    'tourist_segment',
)


def get_tourism_metrics(db_path, filters):
    actual_filters = filters or {}
    where, params = build_tourism_where(actual_filters)
    conn = sqlite3.connect(db_path)
    try:
        summary = _query_summary(conn, where, params, actual_filters)
        return {
            **summary,
            'type_metrics': _query_type_metrics(conn, where, params),
            'attraction_ranking': _query_attraction_ranking(conn, where, params),
            'satisfaction_trend': _query_satisfaction_trend(conn, where, params),
            'visit_trend': _query_visit_trend(conn, where, params),
            'satisfaction_distribution': _query_satisfaction_distribution(conn, where, params),
            'consumption_structure': _query_consumption(conn, where, params),
            'tourist_profile': _query_tourist_profile(conn, where, params),
            'details': _query_details(conn, where, params),
        }
    finally:
        conn.close()


def get_tourism_summary(db_path, filters):
    actual_filters = filters or {}
    where, params = build_tourism_where(actual_filters)
    conn = sqlite3.connect(db_path)
    try:
        return _query_summary(conn, where, params, actual_filters)
    finally:
        conn.close()


def build_tourism_where(filters):
    clauses = ['1=1']
    params = []
    mapping = {
        'start_date': ('visit_date >= ?', str),
        'end_date': ('visit_date <= ?', str),
        'attraction_type': ('attraction_type = ?', str),
        'attraction_name': ('attraction_name = ?', str),
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


def _query_summary(conn, where, params, filters):
    row = conn.execute(
        f'''SELECT COUNT(*), COUNT(DISTINCT tourist_id), MIN(visit_date), MAX(visit_date),
        AVG(satisfaction), SUM(CASE WHEN satisfaction <= ? THEN 1 ELSE 0 END),
        AVG(total_cost), AVG(stay_duration)
        FROM tourism_visit {where}''',
        [LOW_SATISFACTION_MAX, *params],
    ).fetchone() or (0, 0, '', '', 0, 0, 0, 0)
    visit_count = int(row[0] or 0)
    low_count = int(row[5] or 0)
    return {
        'source': _filtered_source(conn, row, filters),
        'visit_count': visit_count,
        'tourist_count': int(row[1] or 0),
        'average_satisfaction': round(row[4] or 0, 2),
        'low_satisfaction_count': low_count,
        'low_satisfaction_rate': round(low_count / visit_count, 4) if visit_count else 0,
        'average_total_cost': round(row[6] or 0, 2),
        'average_stay_duration': round(row[7] or 0, 2),
    }


def _filtered_source(conn, row, filters):
    result = dict(latest_source_from_connection(conn))
    total = result.get('row_count') or result.get('record_count') or 0
    result['total_record_count'] = total
    result['record_count'] = int(row[0] or 0)
    result['date_range'] = {'start': row[2] or '', 'end': row[3] or ''}
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
