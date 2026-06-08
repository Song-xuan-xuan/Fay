from flask import jsonify, request

from core import auth_service
from core.dashboard_service import DashboardService


def _current_is_admin():
    current = auth_service.current_user() or {}
    return current.get('role') == 'admin'


def _service():
    return DashboardService()


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
