from flask import jsonify, request

from core import audit_service
from core import auth_service
from core import member_db


MIN_PASSWORD_LENGTH = 8
VALID_ROLES = {'admin', 'user'}


def _json_data():
    return request.get_json(silent=True) or {}


def _client_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()


def _public_user(user):
    if not user:
        return None
    sanitized = dict(user)
    sanitized.pop('password_hash', None)
    return sanitized


def _current_admin():
    return auth_service.current_user() or {'uid': 0, 'username': ''}


def _log_admin_action(action, resource='', details=None):
    admin = _current_admin()
    audit_service.new_instance().log(
        user_id=admin.get('uid', 0),
        username=admin.get('username', ''),
        action=action,
        resource=resource,
        details=details or {},
        ip_address=_client_ip(),
    )


def _validate_password(password):
    if not password:
        return '密码不能为空'
    if len(str(password)) < MIN_PASSWORD_LENGTH:
        return f'密码长度不能少于 {MIN_PASSWORD_LENGTH} 位'
    return None


def _validate_username(username):
    if not username:
        return '用户名不能为空'
    if username == 'User':
        return '不能使用保留的用户名 "User"'
    if username.lower() == 'admin':
        return '不能使用保留的用户名 "admin"'
    if len(username) > 64:
        return '用户名不能超过 64 个字符'
    if any(char.isspace() for char in username):
        return '用户名不能包含空白字符'
    return None


def register_auth_routes(app):
    if app.config.get('FAY_AUTH_ROUTES_REGISTERED'):
        return
    app.config['FAY_AUTH_ROUTES_REGISTERED'] = True

    @app.route('/api/auth/login', methods=['POST'])
    def api_auth_login():
        data = _json_data()
        username = str(data.get('username') or '').strip()
        password = str(data.get('password') or '')
        db = member_db.new_instance()
        audit = audit_service.new_instance()
        if not username or not password:
            return jsonify({'error': '用户名和密码不能为空'}), 400
        if not db.verify_password(username, password):
            audit.log(0, username, 'login_failed', details={}, ip_address=_client_ip())
            return jsonify({'error': '用户名或密码错误'}), 401
        user = db.get_user_by_username(username)
        db.touch_last_login(user['uid'])
        audit.log(user['uid'], username, 'login_success', details={}, ip_address=_client_ip())
        return jsonify(auth_service.login_response_payload(user))

    @app.route('/api/auth/register', methods=['POST'])
    def api_auth_register():
        data = _json_data()
        username = str(data.get('username') or '').strip()
        password = str(data.get('password') or '')
        email = str(data.get('email') or '').strip()
        error = _validate_username(username) or _validate_password(password)
        if error:
            return jsonify({'error': error}), 400
        db = member_db.new_instance()
        if db.is_username_exist(username) != 'notexists':
            return jsonify({'error': '该用户名已存在'}), 400
        try:
            user = db.create_user_with_password(username, password, role='user', email=email, force_change=False)
        except Exception as exc:
            return jsonify({'error': f'注册失败: {exc}'}), 400
        audit_service.new_instance().log(
            user['uid'],
            user['username'],
            'register',
            details={},
            ip_address=_client_ip(),
        )
        db.touch_last_login(user['uid'])
        return jsonify(auth_service.login_response_payload(user))

    @app.route('/api/auth/logout', methods=['POST'])
    @auth_service.require_auth
    def api_auth_logout():
        user = _current_admin()
        audit_service.new_instance().log(
            user.get('uid', 0),
            user.get('username', ''),
            'logout',
            details={},
            ip_address=_client_ip(),
        )
        return jsonify({'success': True})

    @app.route('/api/auth/me', methods=['GET'])
    @auth_service.require_auth
    def api_auth_me():
        current = auth_service.current_user()
        user = member_db.new_instance().get_user_by_uid(current.get('uid'), include_hash=False)
        if not user or int(user.get('is_active') or 0) != 1:
            return jsonify({'error': '用户不存在或已禁用'}), 401
        user['must_change_password'] = member_db.new_instance().must_change_password(user['username'])
        return jsonify(user)

    @app.route('/api/auth/change-password', methods=['POST'])
    @auth_service.require_auth
    def api_auth_change_password():
        data = _json_data()
        current = auth_service.current_user()
        old_password = str(data.get('old_password') or '')
        new_password = str(data.get('new_password') or '')
        error = _validate_password(new_password)
        if error:
            return jsonify({'error': error}), 400
        db = member_db.new_instance()
        if not db.change_password(current.get('username'), old_password, new_password):
            return jsonify({'error': '旧密码错误'}), 400
        user = db.get_user_by_username(current.get('username'))
        audit_service.new_instance().log(
            user['uid'],
            user['username'],
            'password_change',
            details={},
            ip_address=_client_ip(),
        )
        return jsonify({'success': True, 'token': auth_service.issue_login_token(user)})

    @app.route('/api/users', methods=['GET'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_users_list():
        return jsonify({'list': member_db.new_instance().list_users()})

    @app.route('/api/users', methods=['POST'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_users_create():
        data = _json_data()
        username = str(data.get('username') or '').strip()
        password = str(data.get('password') or '')
        role = str(data.get('role') or 'user').strip()
        email = str(data.get('email') or '').strip()
        if not username:
            return jsonify({'error': '用户名不能为空'}), 400
        if role not in VALID_ROLES:
            return jsonify({'error': '角色无效'}), 400
        error = _validate_password(password)
        if error:
            return jsonify({'error': error}), 400
        try:
            user = member_db.new_instance().create_user_with_password(username, password, role=role, email=email)
        except Exception as exc:
            return jsonify({'error': f'创建用户失败: {exc}'}), 400
        _log_admin_action('user_create', f"uid={user['uid']}", {'username': username, 'role': role})
        public_user = _public_user(user)
        return jsonify({'success': True, 'uid': public_user['uid'], 'user': public_user})

    @app.route('/api/users/<int:uid>', methods=['PUT'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_users_update(uid):
        data = _json_data()
        role = data.get('role')
        if role is not None:
            role = str(role).strip()
            if role not in VALID_ROLES:
                return jsonify({'error': '角色无效'}), 400
        email = data.get('email')
        is_active = data.get('is_active')
        user = member_db.new_instance().update_user_auth(uid, role=role, email=email, is_active=is_active)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        _log_admin_action('user_update', f'uid={uid}', {'role': role, 'email': email, 'is_active': is_active})
        return jsonify({'success': True, 'user': _public_user(user)})

    @app.route('/api/users/<int:uid>', methods=['DELETE'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_users_delete(uid):
        db = member_db.new_instance()
        user = db.get_user_by_uid(uid, include_hash=False)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        db.delete_user(user['username'])
        _log_admin_action('user_delete', f'uid={uid}', {'username': user['username']})
        return jsonify({'success': True})

    @app.route('/api/users/<int:uid>/reset-password', methods=['POST'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_users_reset_password(uid):
        data = _json_data()
        new_password = str(data.get('new_password') or '')
        error = _validate_password(new_password)
        if error:
            return jsonify({'error': error}), 400
        db = member_db.new_instance()
        if not db.get_user_by_uid(uid):
            return jsonify({'error': '用户不存在'}), 404
        db.reset_password(uid, new_password, force_change=True)
        _log_admin_action('password_reset', f'uid={uid}', {})
        return jsonify({'success': True})

    @app.route('/api/audit-logs', methods=['GET'])
    @auth_service.require_auth
    @auth_service.require_role('admin')
    def api_audit_logs():
        result = audit_service.new_instance().list_logs(
            username=request.args.get('username'),
            action=request.args.get('action'),
            limit=request.args.get('limit', 50),
            offset=request.args.get('offset', 0),
        )
        return jsonify(result)
