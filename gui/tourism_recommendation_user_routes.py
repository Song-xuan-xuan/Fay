from flask import jsonify, request

from core import auth_service
from gui.tourism_recommendation_route_utils import (
    current_user_id,
    json_data,
    login_required_response,
    ok,
    service,
)


def register_recommendation_user_routes(app):
    _register_preference_routes(app)
    _register_recommendation_routes(app)
    _register_history_routes(app)
    _register_feedback_routes(app)


def _register_preference_routes(app):
    @app.route('/api/recommendation/preferences', methods=['GET'])
    @auth_service.require_auth
    def api_get_recommendation_preferences():
        blocked = login_required_response()
        if blocked:
            return blocked
        return ok(preferences=service().get_user_preferences(current_user_id()))

    @app.route('/api/recommendation/preferences', methods=['PUT'])
    @auth_service.require_auth
    def api_save_recommendation_preferences():
        blocked = login_required_response()
        if blocked:
            return blocked
        return ok(preferences=service().save_user_preferences(current_user_id(), json_data()))

    @app.route('/api/recommendation/preferences', methods=['DELETE'])
    @auth_service.require_auth
    def api_delete_recommendation_preferences():
        blocked = login_required_response()
        if blocked:
            return blocked
        service().delete_user_preferences(current_user_id())
        return ok()


def _register_recommendation_routes(app):
    @app.route('/api/recommendation/recommend', methods=['POST'])
    @auth_service.require_auth
    def api_create_recommendation():
        blocked = login_required_response()
        if blocked:
            return blocked
        payload = json_data()
        payload['user_id'] = current_user_id()
        return jsonify(service().recommend(payload))


def _register_history_routes(app):
    @app.route('/api/recommendation/history', methods=['GET'])
    @auth_service.require_auth
    def api_list_recommendation_history():
        blocked = login_required_response()
        if blocked:
            return blocked
        limit = request.args.get('limit', 20)
        return ok(items=service().list_recommendations(user_id=current_user_id(), limit=limit))

    @app.route('/api/recommendation/history/<int:recommendation_id>', methods=['GET'])
    @auth_service.require_auth
    def api_get_recommendation_history(recommendation_id):
        blocked = login_required_response()
        if blocked:
            return blocked
        item = service().get_recommendation(recommendation_id, user_id=current_user_id())
        if not item:
            return jsonify({'error': '推荐记录不存在'}), 404
        return ok(item=item)


def _register_feedback_routes(app):
    @app.route('/api/recommendation/feedback', methods=['POST'])
    @auth_service.require_auth
    def api_submit_recommendation_feedback():
        blocked = login_required_response()
        if blocked:
            return blocked
        data = json_data()
        feedback = service().submit_feedback(
            data.get('recommendation_id'), current_user_id(), data.get('action', ''),
            data.get('rating'), data.get('comment', ''),
        )
        return ok(feedback=feedback)
