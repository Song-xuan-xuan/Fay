import functools
import json
import os
import secrets
import time
from datetime import datetime, timedelta, timezone

import jwt
from flask import jsonify, request

from utils import config_util, util


JWT_ALGORITHM = 'HS256'
SECRET_FILE = os.path.join('memory', '.jwt_secret')
DEFAULT_EXPIRATION_HOURS = 168


def _read_config_file():
    try:
        with open('config.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception:
        return {}


def get_auth_config():
    if isinstance(config_util.config, dict):
        return config_util.config.get('auth', {}) or {}
    return (_read_config_file().get('auth') or {})


def auth_enabled():
    value = get_auth_config().get('enabled', False)
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')


def get_jwt_secret():
    configured = str(get_auth_config().get('jwt_secret') or '').strip()
    if configured and configured != 'your-secret-key-change-me-in-production':
        return configured
    os.makedirs(os.path.dirname(SECRET_FILE), exist_ok=True)
    if os.path.exists(SECRET_FILE):
        with open(SECRET_FILE, 'r', encoding='utf-8') as file:
            return file.read().strip()
    secret = secrets.token_urlsafe(32)
    with open(SECRET_FILE, 'w', encoding='utf-8') as file:
        file.write(secret)
    util.log(1, f'已生成新的 JWT 密钥文件: {SECRET_FILE}')
    return secret


def _expiration_hours():
    raw_value = get_auth_config().get('jwt_expiration_hours', DEFAULT_EXPIRATION_HOURS)
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return DEFAULT_EXPIRATION_HOURS


def generate_token(username, role, uid):
    now = datetime.now(timezone.utc)
    payload = {
        'username': username,
        'role': role,
        'uid': int(uid),
        'iat': now,
        'exp': now + timedelta(hours=_expiration_hours()),
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)


def verify_token(token):
    try:
        return jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise ValueError('Token 已过期') from exc
    except jwt.InvalidTokenError as exc:
        raise ValueError('无效的 Token') from exc


def _extract_bearer_token():
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    return auth_header.split(' ', 1)[1].strip()


def require_auth(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        enabled = auth_enabled()
        token = _extract_bearer_token()
        if not token:
            if not enabled:
                return func(*args, **kwargs)
            return jsonify({'error': '未授权'}), 401
        try:
            request.current_user = verify_token(token)
        except ValueError as exc:
            if not enabled:
                return func(*args, **kwargs)
            return jsonify({'error': str(exc)}), 401
        return func(*args, **kwargs)
    return wrapper


def require_role(*roles):
    allowed_roles = set(roles)

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_user = getattr(request, 'current_user', None)
            if current_user is None:
                if not auth_enabled():
                    return func(*args, **kwargs)
                return jsonify({'error': '未授权'}), 401
            if current_user.get('role') not in allowed_roles:
                return jsonify({'error': '权限不足'}), 403
            return func(*args, **kwargs)
        return wrapper
    return decorator


def current_user():
    return getattr(request, 'current_user', None)


def issue_login_token(user):
    return generate_token(user['username'], user['role'], user['uid'])


def login_response_payload(user):
    from core import member_db

    return {
        'token': issue_login_token(user),
        'username': user['username'],
        'role': user['role'],
        'uid': user['uid'],
        'email': user.get('email') or '',
        'avatar_path': user.get('avatar_path') or '',
        'must_change_password': member_db.new_instance().must_change_password(user['username']),
        'expires_in': _expiration_hours() * 3600,
        'server_time': int(time.time()),
    }
