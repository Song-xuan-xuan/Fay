#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
from datetime import datetime
from typing import Any, Callable, Dict, Iterable, Optional
from urllib.parse import urlparse

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from core import audit_service
from core import auth_service
from utils import util


KB_LIBRARY_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'library'))
KB_ALLOWED_EXTENSIONS = {'.docx', '.pdf'}
KB_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*]')


def _serialize_for_json(obj: Any):
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(key): _serialize_for_json(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_serialize_for_json(item) for item in obj]
    if hasattr(obj, '__dict__'):
        return {key: _serialize_for_json(value) for key, value in vars(obj).items()}
    return str(obj)


def _is_local_hostname(hostname: str) -> bool:
    value = str(hostname or '').strip().lower()
    return value in {'localhost', '127.0.0.1', '::1'} or value.startswith('127.')


def _request_host_name() -> str:
    return (urlparse(f"//{request.host}").hostname or '').lower()


def _is_allowed_kb_source(source_url: str) -> bool:
    source_host = (urlparse(source_url).hostname or '').lower()
    target_host = _request_host_name()
    if not source_host or not target_host:
        return False
    if source_host == target_host:
        return True
    return _is_local_hostname(source_host) and _is_local_hostname(target_host)


def _require_kb_write_access():
    origin = (request.headers.get('Origin') or '').strip()
    referer = (request.headers.get('Referer') or '').strip()
    if origin:
        if _is_allowed_kb_source(origin):
            return None
        return jsonify({"success": False, "error": "拒绝跨来源知识库写请求"}), 403
    if referer:
        if _is_allowed_kb_source(referer):
            return None
        return jsonify({"success": False, "error": "拒绝跨来源知识库写请求"}), 403
    if _is_local_hostname(request.remote_addr or ''):
        return None
    return jsonify({"success": False, "error": "知识库写接口仅允许本机或同源请求"}), 403


def _client_ip() -> str:
    return request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()


def _audit_knowledge_action(action: str, resource: str = '', details: Optional[Dict[str, Any]] = None):
    try:
        current = auth_service.current_user() or {}
        audit_service.new_instance().log(
            user_id=current.get('uid', 0),
            username=current.get('username', ''),
            action=action,
            resource=resource,
            details=details or {},
            ip_address=_client_ip(),
        )
    except Exception as exc:
        util.log(1, f"记录知识库审计日志失败: {exc}")


def _ensure_kb_library_dir() -> str:
    os.makedirs(KB_LIBRARY_DIR, exist_ok=True)
    return KB_LIBRARY_DIR


def _safe_kb_filename(filename: str) -> Optional[str]:
    raw_value = str(filename or '').strip()
    raw_name = os.path.basename(raw_value)
    if not raw_name or raw_name != raw_value or '..' in raw_name:
        return None
    _, ext = os.path.splitext(raw_name)
    if ext.lower() not in KB_ALLOWED_EXTENSIONS:
        return None
    safe_name = KB_INVALID_FILENAME_CHARS.sub('_', raw_name).strip(' .')
    if not safe_name:
        safe_name = secure_filename(f"document{ext.lower()}")
    return safe_name


def _resolve_kb_file_path(filename: str) -> str:
    safe_name = _safe_kb_filename(filename)
    if not safe_name:
        raise ValueError('仅支持 .docx 和 .pdf 文件')
    root = os.path.abspath(_ensure_kb_library_dir())
    target = os.path.abspath(os.path.join(root, safe_name))
    if os.path.commonpath([root, target]) != root:
        raise ValueError('非法文件路径')
    return target


class KnowledgeBaseRoutes:
    def __init__(
        self,
        get_mcp_servers: Callable[[], Iterable[Dict[str, Any]]],
        call_mcp_tool: Callable[..., Any],
    ):
        self.get_mcp_servers = get_mcp_servers
        self.call_mcp_tool = call_mcp_tool
        self.blueprint = Blueprint('knowledge_base', __name__)
        self._register_routes()

    def _register_routes(self):
        self.blueprint.add_url_rule('/api/kb/files', view_func=self.list_files, methods=['GET'])
        self.blueprint.add_url_rule('/api/kb/files/upload', view_func=self.upload_files, methods=['POST'])
        self.blueprint.add_url_rule('/api/kb/files/<path:filename>', view_func=self.delete_file, methods=['DELETE'])
        self.blueprint.add_url_rule('/api/kb/ingest', view_func=self.ingest, methods=['POST'])
        self.blueprint.add_url_rule('/api/kb/query', view_func=self.query, methods=['POST'])
        self.blueprint.add_url_rule('/api/kb/stats', view_func=self.stats, methods=['GET'])

    def find_yueshen_server_id(self) -> Optional[int]:
        for server in self.get_mcp_servers():
            name = str(server.get('name', '')).lower()
            if 'yueshen' in name and 'rag' in name and server.get('status') == 'online':
                return int(server['id'])
        return None

    def call_yueshen_tool(self, method: str, params: Dict[str, Any]):
        server_id = self.find_yueshen_server_id()
        if server_id is None:
            return False, '请先连接 yueshen rag MCP 服务'
        success, result = self.call_mcp_tool(server_id, method, dict(params or {}), skip_enabled_check=True)
        return success, result

    def list_files(self):
        root = _ensure_kb_library_dir()
        files = []
        for name in sorted(os.listdir(root)):
            path = os.path.join(root, name)
            if not os.path.isfile(path):
                continue
            _, ext = os.path.splitext(name)
            if ext.lower() not in KB_ALLOWED_EXTENSIONS:
                continue
            stat = os.stat(path)
            files.append({
                "name": name,
                "size": stat.st_size,
                "mtime": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            })
        return jsonify({"success": True, "library_dir": root, "files": files})

    def upload_files(self):
        access_error = _require_kb_write_access()
        if access_error:
            return access_error
        uploaded = request.files.getlist('files')
        if not uploaded:
            single = request.files.get('file')
            uploaded = [single] if single else []
        if not uploaded:
            return jsonify({"success": False, "error": "未选择文件"}), 400

        saved = []
        errors = []
        for item in uploaded:
            try:
                target = _resolve_kb_file_path(item.filename)
                item.save(target)
                saved.append({"name": os.path.basename(target), "size": os.path.getsize(target)})
            except Exception as exc:
                errors.append({"name": item.filename, "error": str(exc)})

        status = 200 if saved else 400
        if saved:
            _audit_knowledge_action(
                'knowledge_upload',
                'library',
                {'files': [item['name'] for item in saved], 'count': len(saved)},
            )
        return jsonify({
            "success": bool(saved),
            "library_dir": _ensure_kb_library_dir(),
            "files": saved,
            "errors": errors,
        }), status

    def delete_file(self, filename):
        access_error = _require_kb_write_access()
        if access_error:
            return access_error
        try:
            target = _resolve_kb_file_path(filename)
        except ValueError as exc:
            return jsonify({"success": False, "error": str(exc)}), 400
        if not os.path.exists(target):
            return jsonify({"success": False, "error": "文件不存在"}), 404
        os.remove(target)
        deleted = os.path.basename(target)
        _audit_knowledge_action('knowledge_delete', f'file={deleted}', {'filename': deleted})
        return jsonify({"success": True, "deleted": deleted})

    def ingest(self):
        access_error = _require_kb_write_access()
        if access_error:
            return access_error
        data = request.json or {}
        params = {
            "corpus_dir": _ensure_kb_library_dir(),
            "reset": bool(data.get("reset", False)),
            "chunk_size": int(data.get("chunk_size", 600)),
            "overlap": int(data.get("overlap", 120)),
            "batch_size": int(data.get("batch_size", 32)),
        }
        success, result = self.call_yueshen_tool("ingest_yueshen", params)
        status = 200 if success else 500
        return jsonify({"success": success, "result": _serialize_for_json(result)}), status

    def query(self):
        data = request.json or {}
        query = str(data.get("query", "")).strip()
        if not query:
            return jsonify({"success": False, "error": "query 不能为空"}), 400
        params = {"query": query, "top_k": int(data.get("top_k", 5))}
        success, result = self.call_yueshen_tool("query_yueshen", params)
        status = 200 if success else 500
        return jsonify({"success": success, "result": _serialize_for_json(result)}), status

    def stats(self):
        success, result = self.call_yueshen_tool("yueshen_stats", {})
        status = 200 if success else 500
        return jsonify({
            "success": success,
            "library_dir": _ensure_kb_library_dir(),
            "result": _serialize_for_json(result),
        }), status


def register_kb_routes(
    app,
    get_mcp_servers: Callable[[], Iterable[Dict[str, Any]]],
    call_mcp_tool: Callable[..., Any],
):
    routes = KnowledgeBaseRoutes(get_mcp_servers, call_mcp_tool)
    app.register_blueprint(routes.blueprint)
