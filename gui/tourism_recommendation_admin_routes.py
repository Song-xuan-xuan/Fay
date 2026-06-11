from flask import Response, jsonify, request, send_file

from core import auth_service
from gui.tourism_recommendation_route_utils import (
    admin_required_response,
    attraction_csv,
    attraction_xlsx,
    csv_rows,
    is_dry_run,
    json_data,
    ok,
    service,
    xlsx_rows,
)


def _guard():
    return admin_required_response()


def register_recommendation_admin_routes(app):
    _register_catalog_routes(app)
    _register_material_config_routes(app)
    _register_import_export_routes(app)


def _register_catalog_routes(app):
    _register_attraction_routes(app)
    _register_template_routes(app)
    _register_stop_routes(app)


def _register_attraction_routes(app):
    @app.route('/api/recommendation/admin/attractions', methods=['GET', 'POST'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_admin_attractions():
        blocked = _guard()
        if blocked:
            return blocked
        if request.method == 'GET':
            return ok(items=service().list_attractions())
        return ok(id=service().upsert_attraction(json_data()))

    @app.route('/api/recommendation/admin/attractions/<int:item_id>', methods=['PUT', 'DELETE'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_admin_attraction_detail(item_id):
        blocked = _guard()
        if blocked:
            return blocked
        if request.method == 'DELETE':
            service().delete_attraction(item_id)
            return ok()
        data = json_data()
        data['id'] = item_id
        return ok(id=service().upsert_attraction(data))


def _register_template_routes(app):
    @app.route('/api/recommendation/admin/templates', methods=['GET', 'POST'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_admin_templates():
        blocked = _guard()
        if blocked:
            return blocked
        if request.method == 'GET':
            return ok(items=service().list_route_templates())
        return ok(id=service().upsert_route_template(json_data()))

    @app.route('/api/recommendation/admin/templates/<int:item_id>', methods=['PUT', 'DELETE'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_admin_template_detail(item_id):
        blocked = _guard()
        if blocked:
            return blocked
        if request.method == 'DELETE':
            service().delete_route_template(item_id)
            return ok()
        data = json_data()
        data['id'] = item_id
        return ok(id=service().upsert_route_template(data))


def _register_stop_routes(app):
    @app.route('/api/recommendation/admin/templates/<int:template_id>/stops', methods=['GET', 'POST'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_admin_template_stops(template_id):
        blocked = _guard()
        if blocked:
            return blocked
        if request.method == 'GET':
            return ok(items=service().list_route_stops(template_id))
        data = json_data()
        return ok(id=service().upsert_route_stop(
            template_id, data.get('attraction_id'), data.get('order_index', 0),
            data.get('stay_minutes', 30), id=data.get('id'), note=data.get('note', ''),
        ))


def _register_material_config_routes(app):
    _register_stop_delete_routes(app)
    _register_edge_routes(app)
    _register_material_routes(app)
    _register_config_routes(app)


def _register_stop_delete_routes(app):
    @app.route('/api/recommendation/admin/stops/<int:item_id>', methods=['DELETE'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_admin_delete_stop(item_id):
        blocked = _guard()
        if blocked:
            return blocked
        service().delete_route_stop(item_id)
        return ok()


def _register_edge_routes(app):
    @app.route('/api/recommendation/admin/edges', methods=['GET', 'POST'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_admin_edges():
        blocked = _guard()
        if blocked:
            return blocked
        if request.method == 'GET':
            return ok(items=service().list_route_edges())
        data = json_data()
        edge_data = {key: value for key, value in data.items() if key not in ('from_attraction_id', 'to_attraction_id')}
        return ok(id=service().upsert_route_edge(data.get('from_attraction_id'), data.get('to_attraction_id'), **edge_data))

    @app.route('/api/recommendation/admin/edges/<int:item_id>', methods=['DELETE'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_admin_delete_edge(item_id):
        blocked = _guard()
        if blocked:
            return blocked
        service().delete_route_edge(item_id)
        return ok()


def _register_material_routes(app):
    @app.route('/api/recommendation/admin/materials', methods=['GET', 'POST'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_admin_materials():
        blocked = _guard()
        if blocked:
            return blocked
        if request.method == 'GET':
            return ok(items=service().list_explanation_materials(request.args.get('attraction_id')))
        data = json_data()
        return ok(id=service().upsert_explanation_material(
            data.get('attraction_id'), data.get('interest_tag', ''),
            data.get('title', ''), data.get('script', ''), id=data.get('id'), focus=data.get('focus', ''),
        ))

    @app.route('/api/recommendation/admin/materials/<int:item_id>', methods=['DELETE'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_admin_delete_material(item_id):
        blocked = _guard()
        if blocked:
            return blocked
        service().delete_explanation_material(item_id)
        return ok()


def _register_config_routes(app):
    @app.route('/api/recommendation/admin/config', methods=['GET', 'PUT'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_admin_config():
        blocked = _guard()
        if blocked:
            return blocked
        svc = service()
        return ok(config=svc.get_config() if request.method == 'GET' else svc.update_config(json_data()))


def _register_import_export_routes(app):
    _register_log_routes(app)
    _register_json_transfer_routes(app)
    _register_attraction_transfer_routes(app)
    _register_initialize_routes(app)


def _register_log_routes(app):
    @app.route('/api/recommendation/admin/logs', methods=['GET'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_admin_logs():
        blocked = _guard()
        if blocked:
            return blocked
        return ok(items=service().list_recommendations(limit=request.args.get('limit', 50)))


def _register_json_transfer_routes(app):
    @app.route('/api/recommendation/admin/export', methods=['GET'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_admin_export_all():
        blocked = _guard()
        if blocked:
            return blocked
        return jsonify(service().export_data())

    @app.route('/api/recommendation/admin/import', methods=['POST'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_admin_import_all():
        blocked = _guard()
        if blocked:
            return blocked
        data = json_data()
        return jsonify(service().import_data(data, dry_run=bool(data.get('dry_run'))))


def _register_attraction_transfer_routes(app):
    @app.route('/api/recommendation/admin/attractions/export', methods=['GET'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_admin_export_attractions():
        blocked = _guard()
        if blocked:
            return blocked
        items = service().list_attractions()
        if request.args.get('format') == 'xlsx':
            return send_file(attraction_xlsx(items), as_attachment=True, download_name='recommendation_attractions.xlsx')
        return Response(attraction_csv(items), mimetype='text/csv')

    @app.route('/api/recommendation/admin/attractions/import', methods=['POST'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_admin_import_attractions():
        blocked = _guard()
        if blocked:
            return blocked
        upload = request.files.get('file')
        if not upload or not upload.filename:
            return jsonify({'error': '请选择导入文件'}), 400
        rows = xlsx_rows(upload) if upload.filename.lower().endswith('.xlsx') else csv_rows(upload)
        return jsonify(service().import_attractions(rows, dry_run=is_dry_run()))


def _register_initialize_routes(app):
    @app.route('/api/recommendation/admin/initialize-attractions', methods=['POST'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_admin_initialize_attractions():
        blocked = _guard()
        if blocked:
            return blocked
        return jsonify(service().initialize_attractions_from_tourism(json_data().get('limit', 100)))
