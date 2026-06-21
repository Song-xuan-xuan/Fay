from flask import Response, jsonify, request

from core import auth_service
from core.dashboard_service import DASHBOARD_ATTRACTIONS, DEFAULT_DASHBOARD_ATTRACTION, DashboardService
from core.visitor_report_service import VisitorReportService


def _current_is_admin():
    current = auth_service.current_user() or {}
    return current.get('role') == 'admin'


def _service():
    return DashboardService()


def _visitor_service():
    return VisitorReportService()


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ('1', 'true', 'yes', 'y', 'on')
    return bool(value)


def _dashboard_speak_username(payload):
    current = auth_service.current_user() or {}
    requested = str(payload.get('username') or payload.get('user') or '').strip()
    if not current:
        return requested or 'User'
    if current.get('role') == 'admin':
        return requested or current.get('username') or 'User'
    return current.get('username') or requested or 'User'


def _send_dashboard_speech(text, username):
    if not text or not str(text).strip():
        return False, '解读内容为空'
    try:
        import uuid
        import fay_booter
        from core import stream_manager
        from core.interact import Interact

        fay = getattr(fay_booter, 'feiFei', None)
        if fay is None:
            return False, 'Fay 运行实例未初始化'
        conversation_id = 'dashboard_' + str(uuid.uuid4())
        stream_manager.new_instance().set_current_conversation(username or 'User', conversation_id, session_type='dashboard_explain')
        stream_manager.new_instance().set_stop_generation(username or 'User', stop=False)
        fay.say(Interact('dashboard_explain', 2, {
            'user': username or 'User',
            'msg': '',
            'conversation_id': conversation_id,
            'isend': True,
            'isfirst': True,
            'no_record': True,
            'no_panel': True,
        }), str(text))
        return True, ''
    except Exception as exc:
        return False, str(exc)


def _dashboard_attraction(value):
    name = str(value or '').strip()
    if name in DASHBOARD_ATTRACTIONS:
        return name
    return DEFAULT_DASHBOARD_ATTRACTION


def _dashboard_tourism_filters():
    return {
        'start_date': request.args.get('start_date'),
        'end_date': request.args.get('end_date'),
        'attraction_type': request.args.get('attraction_type'),
        'attraction_name': _dashboard_attraction(request.args.get('attraction_name')),
        'satisfaction_min': request.args.get('satisfaction_min'),
        'satisfaction_max': request.args.get('satisfaction_max'),
        'tourist_segment': request.args.get('tourist_segment'),
    }


def register_dashboard_routes(app):
    if app.config.get('FAY_DASHBOARD_ROUTES_REGISTERED'):
        return
    app.config['FAY_DASHBOARD_ROUTES_REGISTERED'] = True

    @app.route('/api/dashboard/overview', methods=['GET'])
    @auth_service.require_auth
    def api_dashboard_overview():
        range_key = request.args.get('range', '7d')
        filters = _dashboard_tourism_filters()
        return jsonify(_service().get_overview(range_key, is_admin=_current_is_admin(), tourism_filters=filters))

    @app.route('/api/dashboard/service-trends', methods=['GET'])
    @auth_service.require_auth
    def api_dashboard_service_trends():
        range_key = request.args.get('range', '7d')
        return jsonify(_service().get_service_trends(range_key))

    @app.route('/api/dashboard/hot-topics', methods=['GET'])
    @auth_service.require_auth
    def api_dashboard_hot_topics():
        range_key = request.args.get('range', '7d')
        return jsonify(_service().get_hot_topics(range_key))

    @app.route('/api/dashboard/tourism', methods=['GET'])
    @auth_service.require_auth
    def api_dashboard_tourism():
        return jsonify(_service().get_tourism(_dashboard_tourism_filters()))

    @app.route('/api/dashboard/users', methods=['GET'])
    @auth_service.require_auth
    def api_dashboard_users():
        return jsonify(_service().get_user_metrics(is_admin=_current_is_admin()))

    @app.route('/api/dashboard/tourism/reimport', methods=['POST'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_dashboard_tourism_reimport():
        return jsonify(_service().import_tourism_excel(force=True))

    @app.route('/api/dashboard/explain', methods=['POST'])
    @auth_service.require_auth
    def api_dashboard_explain():
        data = request.get_json(silent=True) or {}
        if not isinstance(data, dict):
            data = {}
        result = _service().explain(data)
        result['spoken'] = False
        if _as_bool(data.get('speak')):
            username = _dashboard_speak_username(data)
            spoken, error = _send_dashboard_speech(result.get('text'), username)
            result['spoken'] = spoken
            result['speaker_username'] = username
            if error:
                result['speak_error'] = error
        return jsonify(result)

    @app.route('/api/dashboard/visitor-report/generate', methods=['POST'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_dashboard_visitor_report_generate():
        data = request.get_json(silent=True) or {}
        report = _visitor_service().generate_report(
            range_key=data.get('range') or data.get('range_key') or '7d',
            start_ms=data.get('start_ms'),
            end_ms=data.get('end_ms'),
            created_by=(auth_service.current_user() or {}).get('username', 'admin'),
        )
        return jsonify(report)

    @app.route('/api/dashboard/visitor-report/latest', methods=['GET'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_dashboard_visitor_report_latest():
        return jsonify(_visitor_service().latest_report() or {})

    @app.route('/api/dashboard/visitor-report/list', methods=['GET'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_dashboard_visitor_report_list():
        limit = request.args.get('limit', 20)
        return jsonify({'items': _visitor_service().list_reports(limit=limit)})

    @app.route('/api/dashboard/visitor-report/<int:report_id>', methods=['GET'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_dashboard_visitor_report_detail(report_id):
        report = _visitor_service().get_report(report_id)
        if not report:
            return jsonify({'message': '报告不存在'}), 404
        return jsonify(report)

    @app.route('/api/dashboard/visitor-report/<int:report_id>/evidence', methods=['GET'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_dashboard_visitor_report_evidence(report_id):
        return jsonify({'items': _visitor_service().get_evidence(report_id)})

    @app.route('/api/dashboard/visitor-report/<int:report_id>/export', methods=['GET'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_dashboard_visitor_report_export(report_id):
        exported = _visitor_service().export_report(report_id, request.args.get('format', 'md'))
        if not exported:
            return jsonify({'message': '报告不存在'}), 404
        return Response(
            exported['content'],
            mimetype=exported['content_type'],
            headers={'Content-Disposition': f"attachment; filename={exported['filename']}"},
        )

    @app.route('/api/dashboard/visitor-report/action/<int:action_id>/status', methods=['POST'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_dashboard_visitor_report_action_status(action_id):
        data = request.get_json(silent=True) or {}
        try:
            updated = _visitor_service().update_action_status(action_id, data.get('status'))
        except ValueError as exc:
            return jsonify({'message': str(exc)}), 400
        if not updated:
            return jsonify({'message': '建议不存在'}), 404
        return jsonify(updated)
