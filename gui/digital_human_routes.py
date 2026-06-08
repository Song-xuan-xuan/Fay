import os
import uuid

from flask import jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from core import audit_service
from core import auth_service
from core import digital_human_service
from core import live2d_resource_service
from utils import config_util, util


ALLOWED_COVER_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
MAX_COVER_BYTES = 5 * 1024 * 1024
IMAGE_SIGNATURES = {
    "png": (b"\x89PNG\r\n\x1a\n",),
    "jpg": (b"\xff\xd8\xff",),
    "jpeg": (b"\xff\xd8\xff",),
    "gif": (b"GIF87a", b"GIF89a"),
    "webp": (b"RIFF",),
}


def _json_data():
    return request.get_json(silent=True) or {}


def _client_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip()


def _log_admin_action(action, resource="", details=None):
    try:
        current = auth_service.current_user() or {}
        audit_service.new_instance().log(
            user_id=current.get("uid", 0),
            username=current.get("username", ""),
            action=action,
            resource=resource,
            details=details or {},
            ip_address=_client_ip(),
        )
    except Exception as exc:
        util.log(1, f"记录数字人管理审计日志失败: {exc}")


def _load_runtime_config():
    config_util.load_config()
    digital_human_service.ensure_digital_humans_config(config_util.config)


def _response_error(exc, status=400):
    return jsonify({"success": False, "message": str(exc), "error": str(exc)}), status


def _cover_extension(filename):
    safe_name = secure_filename(filename or "")
    _, extension = os.path.splitext(safe_name)
    return extension.lower().lstrip(".")


def _cover_url(filename):
    return f"/digital-humans/covers/{filename}"


def _save_cover(file_storage, human_id):
    extension = _cover_extension(file_storage.filename)
    if extension not in ALLOWED_COVER_EXTENSIONS:
        raise ValueError("封面仅支持 png、jpg、jpeg、webp、gif")
    if request.content_length and request.content_length > MAX_COVER_BYTES:
        raise ValueError("封面文件不能超过 5MB")
    header = file_storage.stream.read(12)
    file_storage.stream.seek(0)
    if not any(header.startswith(signature) for signature in IMAGE_SIGNATURES[extension]):
        raise ValueError("封面文件内容不是有效图片")
    if extension == "webp" and header[8:12] != b"WEBP":
        raise ValueError("封面文件内容不是有效图片")
    cover_dir = digital_human_service.cover_dir()
    os.makedirs(cover_dir, exist_ok=True)
    filename = f"{secure_filename(human_id)}-{uuid.uuid4().hex}.{extension}"
    file_storage.save(os.path.join(cover_dir, filename))
    return _cover_url(filename)


def register_digital_human_routes(app):
    if app.config.get("FAY_DIGITAL_HUMAN_ROUTES_REGISTERED"):
        return
    app.config["FAY_DIGITAL_HUMAN_ROUTES_REGISTERED"] = True

    @app.route("/api/digital-humans", methods=["GET"])
    @auth_service.require_auth
    @auth_service.require_role("admin")
    def api_list_digital_humans():
        try:
            _load_runtime_config()
            keyword = request.args.get("keyword", "")
            human_type = request.args.get("type", "")
            items = digital_human_service.list_digital_humans(keyword, human_type)
            active = digital_human_service.get_active_digital_human()
            return jsonify({
                "success": True,
                "items": items,
                "active": active,
                "active_id": config_util.config["digital_humans"]["active_id"],
            })
        except Exception as exc:
            return _response_error(exc, 500)

    @app.route("/api/digital-humans/active", methods=["GET"])
    @auth_service.require_auth
    def api_active_digital_human():
        try:
            _load_runtime_config()
            active = digital_human_service.get_active_digital_human()
            return jsonify({"success": True, "digital_human": active})
        except Exception as exc:
            return _response_error(exc, 500)

    @app.route("/api/digital-humans", methods=["POST"])
    @auth_service.require_auth
    @auth_service.require_role("admin")
    def api_create_digital_human():
        try:
            _load_runtime_config()
            human = digital_human_service.create_digital_human(_json_data())
            _log_admin_action("digital_human_create", human.get("id"), {"name": human.get("name")})
            return jsonify({"success": True, "digital_human": human})
        except ValueError as exc:
            return _response_error(exc, 400)
        except Exception as exc:
            return _response_error(exc, 500)

    @app.route("/api/digital-humans/import-live2d-resources", methods=["POST"])
    @auth_service.require_auth
    @auth_service.require_role("admin")
    def api_import_live2d_resources():
        try:
            _load_runtime_config()
            payload = _json_data()
            render_base_url = payload.get("render_base_url") or live2d_resource_service.DEFAULT_RENDER_URL
            result = live2d_resource_service.import_live2d_resource_models(
                render_base_url=render_base_url,
            )
            _log_admin_action(
                "digital_human_import_live2d",
                "live2d_resources",
                {"imported": [item.get("id") for item in result["imported"]]},
            )
            return jsonify({"success": True, **result})
        except ValueError as exc:
            return _response_error(exc, 400)
        except Exception as exc:
            return _response_error(exc, 500)

    @app.route("/api/digital-humans/<human_id>", methods=["PUT"])
    @auth_service.require_auth
    @auth_service.require_role("admin")
    def api_update_digital_human(human_id):
        try:
            _load_runtime_config()
            human = digital_human_service.update_digital_human(human_id, _json_data())
            _log_admin_action("digital_human_update", human.get("id"), {"name": human.get("name")})
            return jsonify({"success": True, "digital_human": human})
        except ValueError as exc:
            return _response_error(exc, 400)
        except Exception as exc:
            return _response_error(exc, 500)

    @app.route("/api/digital-humans/<human_id>", methods=["DELETE"])
    @auth_service.require_auth
    @auth_service.require_role("admin")
    def api_delete_digital_human(human_id):
        try:
            _load_runtime_config()
            human = digital_human_service.delete_digital_human(human_id)
            _log_admin_action("digital_human_delete", human.get("id"), {"name": human.get("name")})
            return jsonify({"success": True, "digital_human": human})
        except ValueError as exc:
            return _response_error(exc, 400)
        except Exception as exc:
            return _response_error(exc, 500)

    @app.route("/api/digital-humans/<human_id>/activate", methods=["POST"])
    @auth_service.require_auth
    @auth_service.require_role("admin")
    def api_activate_digital_human(human_id):
        try:
            _load_runtime_config()
            human = digital_human_service.activate_digital_human(human_id)
            _log_admin_action("digital_human_activate", human.get("id"), {"name": human.get("name")})
            try:
                from core import wsa_server
                web = wsa_server.get_web_instance()
                if web is not None:
                    web.add_cmd({"digitalHuman": human, "digitalHumanActiveId": human.get("id")})
            except Exception as exc:
                util.log(1, f"推送数字人切换消息失败: {exc}")
            return jsonify({"success": True, "digital_human": human})
        except ValueError as exc:
            return _response_error(exc, 400)
        except Exception as exc:
            return _response_error(exc, 500)

    @app.route("/api/digital-humans/<human_id>/cover", methods=["POST"])
    @auth_service.require_auth
    @auth_service.require_role("admin")
    def api_upload_digital_human_cover(human_id):
        try:
            _load_runtime_config()
            cover = request.files.get("cover")
            if not cover or not cover.filename:
                return _response_error(ValueError("请选择封面文件"), 400)
            cover_url = _save_cover(cover, human_id)
            human = digital_human_service.update_digital_human(human_id, {"cover_url": cover_url})
            _log_admin_action("digital_human_cover_update", human.get("id"), {"cover_url": cover_url})
            return jsonify({"success": True, "cover_url": cover_url, "digital_human": human})
        except ValueError as exc:
            return _response_error(exc, 400)
        except Exception as exc:
            return _response_error(exc, 500)

    @app.route("/digital-humans/covers/<path:filename>", methods=["GET"])
    def api_digital_human_cover_file(filename):
        safe_name = secure_filename(filename)
        if safe_name != filename:
            return jsonify({"error": "封面不存在"}), 404
        return send_from_directory(digital_human_service.cover_dir(), safe_name)

    @app.route("/digital-humans/live2d-resources/<model_name>/<path:filename>", methods=["GET"])
    def api_live2d_resource_file(model_name, filename):
        try:
            base_dir, relative_path = live2d_resource_service.resolve_resource_path(model_name, filename)
            return send_from_directory(base_dir, relative_path)
        except ValueError:
            return jsonify({"error": "资源不存在"}), 404
