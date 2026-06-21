from core import auth_service, member_db
from utils import config_util, util


def _auth_config():
    if isinstance(config_util.config, dict):
        return config_util.config.get('auth', {}) or {}
    return {}


def ensure_default_admin():
    auth = _auth_config()
    if not auth_service.auth_enabled():
        return False
    db = member_db.new_instance()
    if db.has_admin_user():
        return False
    username = auth.get('default_admin_username') or 'admin'
    password = auth.get('default_admin_password') or 'admin123'
    db.create_default_admin(username, password)
    util.log(1, f'默认管理员已创建: {username}')
    util.log(1, '请立即修改默认管理员密码')
    return True


def log_auth_status():
    if auth_service.auth_enabled():
        util.log(1, '用户认证已启用')
        return
    util.log(1, '用户认证功能当前处于禁用状态')
