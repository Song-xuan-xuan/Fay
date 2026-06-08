import os
import uuid

from flask import jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from core import audit_service
from core import auth_service
from core import member_db


AVATAR_DIR = os.path.join('cache_data', 'avatars')
ALLOWED_AVATAR_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}
MAX_AVATAR_BYTES = 2 * 1024 * 1024


def _client_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()


def _avatar_extension(filename):
    safe_name = secure_filename(filename or '')
    _, extension = os.path.splitext(safe_name)
    return extension.lower().lstrip('.')


def _avatar_url(filename):
    return f'/avatars/{filename}'


def _avatar_dir():
    return os.path.abspath(AVATAR_DIR)


def _save_avatar_file(file_storage, uid):
    extension = _avatar_extension(file_storage.filename)
    if extension not in ALLOWED_AVATAR_EXTENSIONS:
        raise ValueError('头像仅支持 png、jpg、jpeg、webp、gif')
    if request.content_length and request.content_length > MAX_AVATAR_BYTES:
        raise ValueError('头像文件不能超过 2MB')
    avatar_dir = _avatar_dir()
    os.makedirs(avatar_dir, exist_ok=True)
    filename = f'{int(uid)}-{uuid.uuid4().hex}.{extension}'
    file_storage.save(os.path.join(avatar_dir, filename))
    return _avatar_url(filename)


def register_avatar_routes(app):
    if app.config.get('FAY_AVATAR_ROUTES_REGISTERED'):
        return
    app.config['FAY_AVATAR_ROUTES_REGISTERED'] = True

    @app.route('/api/auth/avatar', methods=['POST'])
    @auth_service.require_auth
    def api_auth_avatar():
        current = auth_service.current_user()
        if not current:
            return jsonify({'error': '未授权'}), 401
        avatar = request.files.get('avatar')
        if not avatar or not avatar.filename:
            return jsonify({'error': '请选择头像文件'}), 400
        try:
            avatar_path = _save_avatar_file(avatar, current.get('uid'))
        except ValueError as exc:
            return jsonify({'error': str(exc)}), 400
        user = member_db.new_instance().update_avatar_path(current.get('uid'), avatar_path)
        audit_service.new_instance().log(
            user['uid'],
            user['username'],
            'avatar_update',
            details={},
            ip_address=_client_ip(),
        )
        return jsonify({'success': True, 'avatar_path': user.get('avatar_path') or ''})

    @app.route('/avatars/<path:filename>', methods=['GET'])
    def api_avatar_file(filename):
        safe_name = secure_filename(filename)
        if safe_name != filename:
            return jsonify({'error': '头像不存在'}), 404
        return send_from_directory(_avatar_dir(), safe_name)
