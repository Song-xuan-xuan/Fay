def is_route_node(stop):
    return (stop.get('node_type') or 'attraction') in ('start', 'end', 'path')


def route_node_stop(stop):
    node_type = stop.get('node_type') or 'path'
    labels = {'start': '起点', 'end': '终点', 'path': '路径节点'}
    return {
        'id': 0,
        'route_stop_id': stop.get('id'),
        'name': stop.get('node_name') or stop.get('note') or labels[node_type],
        'category': labels.get(node_type, '路径节点'),
        'tags': [],
        'stay_minutes': stop.get('stay_minutes') or 0,
        'difficulty': 0,
        'indoor': False,
        'node_type': node_type,
        'score_eligible': False,
        'explanation_focus': stop.get('note') or labels.get(node_type, '路径节点'),
        'script': '',
    }


def attraction_stop(stop, attraction):
    return {
        **attraction,
        'route_stop_id': stop.get('id'),
        'node_type': 'attraction',
        'score_eligible': True,
        'stay_minutes': stop.get('stay_minutes') or attraction.get('visit_minutes', 30),
    }


def is_draft_stop(stop, attraction):
    if not attraction:
        return False
    return (stop.get('node_type') == 'draft') or (not stop.get('enabled') and not attraction.get('enabled'))


def draft_stop(stop, attraction):
    summary = attraction.get('summary') or stop.get('note') or '待管理员确认后补充完整资料。'
    return {
        **attraction,
        'route_stop_id': stop.get('id'),
        'node_type': 'draft',
        'score_eligible': False,
        'stay_minutes': stop.get('stay_minutes') or attraction.get('visit_minutes', 30),
        'explanation_focus': summary,
        'script': f'{summary}（待管理员确认后可补充讲解。）',
    }


def stay_minutes(stop):
    if stop.get('stay_minutes') is not None:
        return int(stop.get('stay_minutes') or 0)
    return int(stop.get('visit_minutes') or 30)
