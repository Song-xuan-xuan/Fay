from flask import Response, jsonify, request

from core import auth_service
from core.dashboard_service import DashboardService
from core.visitor_report_service import VisitorReportService


def _current_is_admin():
    current = auth_service.current_user() or {}
    return current.get('role') == 'admin'


def _service():
    return DashboardService()


def _visitor_service():
    return VisitorReportService()


def register_dashboard_routes(app):
    if app.config.get('FAY_DASHBOARD_ROUTES_REGISTERED'):
        return
    app.config['FAY_DASHBOARD_ROUTES_REGISTERED'] = True

    @app.route('/api/dashboard/overview', methods=['GET'])
    @auth_service.require_auth
    def api_dashboard_overview():
        range_key = request.args.get('range', '7d')
        return jsonify(_service().get_overview(range_key, is_admin=_current_is_admin()))

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
        filters = {
            'start_date': request.args.get('start_date'),
            'end_date': request.args.get('end_date'),
            'attraction_type': request.args.get('attraction_type'),
            'attraction_name': request.args.get('attraction_name'),
            'satisfaction_min': request.args.get('satisfaction_min'),
            'satisfaction_max': request.args.get('satisfaction_max'),
            'tourist_segment': request.args.get('tourist_segment'),
        }
        return jsonify(_service().get_tourism(filters))

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
        return jsonify(_service().explain(request.get_json(silent=True) or {}))

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
