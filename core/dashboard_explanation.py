from core.dashboard_tourism_metrics import TOURISM_FILTER_KEYS


def build_dashboard_explanation(payload, service):
    context = payload if isinstance(payload, dict) else {}
    scope = _explain_scope(context.get('scope'))
    filters = _tourism_filters_from_context(context)
    overview = context.get('overview') if isinstance(context.get('overview'), dict) else {}
    if not overview.get('kpis') or not _overview_matches_filters(overview, filters):
        overview = service.get_overview(context.get('range') or '7d', tourism_filters=filters)
    topics = context.get('topics') if isinstance(context.get('topics'), list) else []
    tourism = context.get('tourism') if isinstance(context.get('tourism'), dict) else {}
    if scope == 'tourism' and not _tourism_snapshot_matches(tourism, filters):
        tourism = service.get_tourism(filters)
    if scope == 'tourism':
        return _tourism_explanation(overview, topics, tourism)
    return _overview_explanation(context, overview, topics)


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


def _overview_explanation(context, overview, topics):
    lookup = _kpi_lookup(overview)
    topic = _top_topic(topics)
    low = _value_text(lookup.get('低满意预警'))
    avg = _value_text(lookup.get('游客平均满意度'))
    attraction = _overview_attraction(overview)
    text = (
        f"全局运营数据统计范围为{_range_text(context.get('range'))}。今日服务人次 {_value_text(lookup.get('今日服务人次'))}，"
        f"本周服务人次 {_value_text(lookup.get('本周服务人次'))}，今日问答次数 {_value_text(lookup.get('今日问答次数'))}。"
        f"全局用户数据中本周活跃 {_value_text(lookup.get('本周活跃用户'))} 人。"
        f"{attraction}旅游数据平均满意度 {avg} 分，"
        f"低满意预警 {low} 条。{_topic_sentence(topic)}"
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


def _tourism_explanation(overview, topics, tourism):
    lookup = _kpi_lookup(overview)
    top = _top_attraction(tourism)
    top_type = _top_type(tourism)
    trend = _latest_satisfaction(tourism)
    avg = _value_text(_first_present(tourism.get('average_satisfaction'), lookup.get('游客平均满意度')))
    low = _value_text(_first_present(tourism.get('low_satisfaction_count'), lookup.get('低满意预警')))
    record_count = _record_count(tourism)
    attraction = _tourism_attraction(tourism)
    text = (
        f"{attraction}景区数据当前累计 {record_count} 条记录，平均满意度 {avg} 分，低满意预警 {low} 条。"
        f"{_top_attraction_sentence(top)}{_top_type_sentence(top_type)}{_trend_sentence(trend)}"
        f"{_topic_sentence(_top_topic(topics))}"
        "建议围绕访问量最高和低满意风险最高的场景，优先优化数字人对交通、门票、排队和服务设施的回答。"
    )
    return {
        'scope': 'tourism',
        'title': f'{attraction}数据解读',
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
    return max(items, key=lambda item: _to_number(item.get('count'))) if items else {}


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


def _overview_matches_filters(overview, filters):
    expected = filters.get('attraction_name')
    if not expected:
        return True
    source = overview.get('tourism_source') if isinstance(overview.get('tourism_source'), dict) else {}
    return source.get('selected_attraction') == expected


def _tourism_snapshot_matches(tourism, filters):
    if not _has_tourism_snapshot(tourism):
        return False
    expected = filters.get('attraction_name')
    if not expected:
        return True
    source = tourism.get('source') if isinstance(tourism.get('source'), dict) else {}
    return source.get('selected_attraction') == expected


def _overview_attraction(overview):
    source = overview.get('tourism_source') if isinstance(overview.get('tourism_source'), dict) else {}
    return source.get('selected_attraction') or '当前景区'


def _tourism_attraction(tourism):
    source = tourism.get('source') if isinstance(tourism.get('source'), dict) else {}
    return source.get('selected_attraction') or '当前景区'


def _top_attraction(tourism):
    items = tourism.get('attraction_ranking') if isinstance(tourism, dict) else []
    items = [item for item in (items or []) if isinstance(item, dict)]
    return max(items, key=lambda item: _to_number(item.get('visits'))) if items else {}


def _top_type(tourism):
    items = tourism.get('type_metrics') if isinstance(tourism, dict) else []
    items = [item for item in (items or []) if isinstance(item, dict)]
    return max(items, key=lambda item: _to_number(item.get('visits'))) if items else {}


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
