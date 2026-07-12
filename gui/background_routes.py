from flask import jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from core import auth_service
from core import background_service


def _response_error(exc, status=400):
    return jsonify({'success': False, 'message': str(exc), 'error': str(exc)}), status


def _background_payload():
    active = background_service.get_active_background()
    return {
        'success': True,
        'items': background_service.list_backgrounds(),
        'active': active,
        'active_id': active['id'],
    }


def register_background_routes(app):
    if app.config.get('FAY_BACKGROUND_ROUTES_REGISTERED'):
        return
    app.config['FAY_BACKGROUND_ROUTES_REGISTERED'] = True

    @app.route('/api/backgrounds', methods=['GET'])
    @auth_service.require_auth
    def api_list_backgrounds():
        return jsonify(_background_payload())

    @app.route('/api/backgrounds/active', methods=['GET'])
    @auth_service.require_auth
    def api_active_background():
        return jsonify({
            'success': True,
            'active': background_service.get_active_background(),
            'active_id': background_service.get_active_id(),
        })

    @app.route('/api/backgrounds', methods=['POST'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_upload_background():
        # 检查是否是 URL 类型
        if request.is_json or request.content_type == 'application/json':
            data = request.get_json()
            url = data.get('url', '').strip()
            name = data.get('name', '').strip()
            if not url:
                return _response_error(ValueError('背景图 URL 不能为空'), 400)
            try:
                item = background_service.add_url_background(url, name)
                return jsonify({'success': True, 'background': item, **_background_payload()})
            except ValueError as exc:
                return _response_error(exc, 400)

        # 原有的文件上传逻辑
        background = request.files.get('background')
        if not background or not background.filename:
            return _response_error(ValueError('请选择背景图文件'), 400)
        try:
            item = background_service.save_background(
                background,
                request.form.get('name', ''),
                request.content_length,
            )
            return jsonify({'success': True, 'background': item, **_background_payload()})
        except ValueError as exc:
            return _response_error(exc, 400)

    @app.route('/api/backgrounds/<background_id>/activate', methods=['POST'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_activate_background(background_id):
        try:
            active = background_service.activate_background(background_id)
            return jsonify({'success': True, 'active': active, **_background_payload()})
        except ValueError as exc:
            return _response_error(exc, 400)

    @app.route('/api/backgrounds/<background_id>', methods=['DELETE'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_delete_background(background_id):
        try:
            result = background_service.delete_background(background_id)
            return jsonify({'success': True, **result})
        except ValueError as exc:
            return _response_error(exc, 400)

    @app.route('/backgrounds/<path:filename>', methods=['GET'])
    def api_background_file(filename):
        safe_name = secure_filename(filename)
        if safe_name != filename:
            return jsonify({'error': '背景图不存在'}), 404
        return send_from_directory(background_service.background_dir(), safe_name)
