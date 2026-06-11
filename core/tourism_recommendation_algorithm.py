import math


DEFAULT_CONFIG = {
    'weights': {
        'interest_match': 0.45,
        'satisfaction': 0.2,
        'popularity': 0.15,
        'time_fit': 0.1,
        'intensity_fit': 0.1,
    },
    'default_walk_minutes': 8,
    'max_alternatives': 2,
}


def build_recommendation(request_data, templates, stops_by_template, attractions, edges, materials, config=None):
    config = _merged_config(config or {})
    candidates = _build_template_candidates(request_data, templates, stops_by_template, attractions, edges, materials, config)
    if not candidates:
        dynamic = _build_dynamic_candidate(request_data, attractions, edges, materials, config)
        candidates = [dynamic] if dynamic else []
    candidates.sort(key=lambda item: (-item['score'], item['name']))
    return _result_payload(request_data, candidates, config)


def _merged_config(config):
    merged = {**DEFAULT_CONFIG, **config}
    merged['weights'] = {**DEFAULT_CONFIG['weights'], **(config.get('weights') or {})}
    return merged


def _build_template_candidates(request_data, templates, stops_by_template, attractions, edges, materials, config):
    candidates = []
    for template in templates:
        if not template.get('enabled'):
            continue
        route_stops, risks = _prepare_stops(template, request_data, stops_by_template, attractions, edges)
        if not route_stops:
            continue
        timeline = _build_timeline(request_data, route_stops, edges, config, risks)
        breakdown = _score_template(request_data, template, route_stops, timeline, config)
        candidates.append(_route_payload(template, route_stops, timeline, breakdown, risks, materials))
    return candidates


def _prepare_stops(template, request_data, stops_by_template, attractions, edges):
    risks = []
    prepared = []
    template_stops = stops_by_template.get(template['id'], [])
    for stop in sorted(template_stops, key=lambda item: item.get('order_index') or 0):
        attraction = attractions.get(stop.get('attraction_id'))
        if attraction and attraction.get('enabled'):
            prepared.append({**attraction, 'stay_minutes': stop.get('stay_minutes') or attraction.get('visit_minutes', 30)})
            continue
        replacement = _replacement_stop(request_data, prepared, attractions, edges)
        if replacement:
            prepared.append(replacement)
            risks.append('原路线存在不可用点位，已自动替换为相近兴趣点。')
        else:
            risks.append('原路线存在不可用点位，且暂无可替换点位。')
    return prepared, risks


def _replacement_stop(request_data, prepared, attractions, edges):
    used = {item['id'] for item in prepared}
    choices = [item for item in attractions.values() if item.get('enabled') and item['id'] not in used]
    if not choices:
        return None
    interests = _string_set(request_data.get('interests'))
    choices.sort(key=lambda item: (-_attraction_score(item, interests), item['name']))
    best = dict(choices[0])
    best['stay_minutes'] = best.get('visit_minutes') or 30
    return best


def _attraction_score(attraction, interests):
    tags = _string_set(attraction.get('tags'))
    interest_score = len(tags & interests) * 100 if interests else 0
    return interest_score + float(attraction.get('satisfaction') or 0) * 10 + float(attraction.get('popularity') or 0)


def _build_timeline(request_data, stops, edges, config, risks):
    current = _parse_time(request_data.get('arrival_time') or '09:00')
    items = []
    total_walk = 0
    previous_id = None
    for stop in stops:
        walk = _walk_minutes(previous_id, stop['id'], edges, config)
        if previous_id and walk == config['default_walk_minutes']:
            risks.append('部分点位步行时间未维护，已使用默认估算。')
        current += walk
        start = current
        current += int(stop.get('stay_minutes') or stop.get('visit_minutes') or 30)
        total_walk += walk
        items.append({**stop, 'walk_minutes': walk, 'start_time': _format_time(start), 'end_time': _format_time(current)})
        previous_id = stop['id']
    return {'items': items, 'total_minutes': current - _parse_time(request_data.get('arrival_time') or '09:00'), 'walk_minutes': total_walk}


def _walk_minutes(from_id, to_id, edges, config):
    if not from_id:
        return 0
    key = (from_id, to_id)
    if key in edges:
        return int(edges[key].get('walk_minutes') or 0)
    reverse = (to_id, from_id)
    if reverse in edges and edges[reverse].get('bidirectional'):
        return int(edges[reverse].get('walk_minutes') or 0)
    return int(config['default_walk_minutes'])


def _score_template(request_data, template, stops, timeline, config):
    interests = _string_set(request_data.get('interests'))
    tags = _string_set(template.get('interest_tags'))
    for stop in stops:
        tags.update(_string_set(stop.get('tags')))
    interest_match = min(1.0, len(tags & interests) / max(1, len(interests))) if interests else 0.5
    satisfaction = _avg([float(item.get('satisfaction') or 0) / 5 for item in stops])
    popularity = _avg([float(item.get('popularity') or 0) / 100 for item in stops])
    time_fit = _time_fit(request_data.get('time_budget_minutes'), timeline['total_minutes'])
    intensity_fit = _intensity_fit(request_data.get('intensity'), stops)
    return _weighted_breakdown(config['weights'], interest_match, satisfaction, popularity, time_fit, intensity_fit)


def _weighted_breakdown(weights, interest_match, satisfaction, popularity, time_fit, intensity_fit):
    values = {
        'interest_match': round(interest_match, 3),
        'satisfaction': round(satisfaction, 3),
        'popularity': round(popularity, 3),
        'time_fit': round(time_fit, 3),
        'intensity_fit': round(intensity_fit, 3),
    }
    values['total'] = round(sum(values[key] * float(weights.get(key, 0)) for key in values), 4)
    return values


def _route_payload(template, stops, timeline, breakdown, risks, materials):
    return {
        'id': template['id'],
        'name': template['name'],
        'summary': template.get('summary') or '',
        'score': breakdown['total'],
        'score_breakdown': breakdown,
        'duration_minutes': timeline['total_minutes'],
        'walk_minutes': timeline['walk_minutes'],
        'intensity': template.get('intensity') or 'medium',
        'budget_level': template.get('budget_level') or '',
        'risks': _unique(risks),
        'stops': [_stop_payload(item, materials) for item in timeline['items']],
    }


def _stop_payload(stop, materials):
    material = _choose_material(stop, materials.get(stop['id'], []))
    return {
        'id': stop['id'],
        'name': stop['name'],
        'category': stop.get('category') or '',
        'tags': stop.get('tags') or [],
        'walk_minutes': stop.get('walk_minutes', 0),
        'stay_minutes': stop.get('stay_minutes') or stop.get('visit_minutes') or 30,
        'start_time': stop.get('start_time'),
        'end_time': stop.get('end_time'),
        'difficulty': stop.get('difficulty') or 1,
        'indoor': bool(stop.get('indoor')),
        'explanation_focus': material.get('focus') or material.get('title') or f"介绍{stop['name']}的核心看点。",
        'script': material.get('script') or f"现在推荐您游览{stop['name']}，这里适合结合您的兴趣重点讲解。",
    }


def _choose_material(stop, options):
    tags = _string_set(stop.get('tags'))
    enabled = [item for item in options if item.get('enabled')]
    for item in enabled:
        if item.get('interest_tag') in tags:
            return item
    return enabled[0] if enabled else {}


def _build_dynamic_candidate(request_data, attractions, edges, materials, config):
    interests = _string_set(request_data.get('interests'))
    choices = [item for item in attractions.values() if item.get('enabled')]
    choices.sort(key=lambda item: (-_attraction_score(item, interests), item['name']))
    chosen = [{**item, 'stay_minutes': item.get('visit_minutes') or 30} for item in choices[:3]]
    if not chosen:
        return None
    template = {'id': 0, 'name': '动态推荐路线', 'summary': '根据兴趣临时组合点位', 'intensity': 'medium'}
    timeline = _build_timeline(request_data, chosen, edges, config, [])
    breakdown = _score_template(request_data, template, chosen, timeline, config)
    return _route_payload(template, chosen, timeline, breakdown, [], materials)


def _result_payload(request_data, candidates, config):
    if not candidates:
        return {'main_route': None, 'alternatives': [], 'message': '暂无可推荐路线'}
    return {
        'request': request_data,
        'main_route': candidates[0],
        'alternatives': candidates[1:1 + int(config.get('max_alternatives', 2))],
        'adjustment_actions': ['缩短行程', '降低强度', '优先室内', '避开拥挤点位'],
    }


def _time_fit(budget, duration):
    if not budget:
        return 0.8
    budget = max(1, int(budget))
    return max(0.0, 1.0 - abs(duration - budget) / budget)


def _intensity_fit(target, stops):
    if not target:
        return 0.8
    target_map = {'low': 1, 'medium': 2, 'high': 3}
    expected = target_map.get(str(target), 2)
    avg_difficulty = _avg([float(item.get('difficulty') or 1) for item in stops])
    return max(0.0, 1.0 - abs(avg_difficulty - expected) / 3)


def _avg(values):
    values = [value for value in values if value is not None]
    return sum(values) / len(values) if values else 0


def _parse_time(value):
    try:
        hour, minute = str(value).split(':', 1)
        return int(hour) * 60 + int(minute)
    except Exception:
        return 9 * 60


def _format_time(value):
    value = int(value) % (24 * 60)
    return f'{value // 60:02d}:{value % 60:02d}'


def _string_set(value):
    if isinstance(value, str):
        value = [item.strip() for item in value.split(',')]
    return {str(item).strip() for item in (value or []) if str(item).strip()}


def _unique(values):
    result = []
    for value in values:
        if value and value not in result:
            result.append(value)
    return result
