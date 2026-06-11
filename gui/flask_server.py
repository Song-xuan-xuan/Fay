# -*- coding: utf-8 -*-
import importlib
import json
import time
import os
import pyaudio
import re
from flask import Flask, render_template, request, jsonify, Response, send_file, send_from_directory, stream_with_context
from flask_cors import CORS
import requests
import datetime
import pytz
import logging
import uuid
from urllib.parse import urlparse, urljoin
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
except Exception:
    ChatOpenAI = None
    HumanMessage = None
    SystemMessage = None
    AIMessage = None
try:
    from langsmith.run_trees import RunTree
except Exception:
    RunTree = None

import fay_booter
from tts import tts_voice
from gevent import pywsgi
try:
    # Use gevent.sleep to avoid blocking the gevent loop; fallback to time.sleep if unavailable
    from gevent import sleep as gsleep
except Exception:
    from time import sleep as gsleep
from scheduler.thread_manager import MyThread
from utils import config_util, util
from core import wsa_server
from core import fay_core
from core import content_db
from core.interact import Interact
from core import member_db
from core import auth_service
from core import audit_service
from core import digital_human_service
from gui.auth_routes import register_auth_routes
from gui.avatar_routes import register_avatar_routes
from gui.dashboard_routes import register_dashboard_routes
from gui.digital_human_routes import register_digital_human_routes
from gui.tourism_recommendation_routes import register_tourism_recommendation_routes
import fay_booter
from flask_httpauth import HTTPBasicAuth
from core import qa_service
from core import stream_manager

# 全局变量，用于跟踪当前的genagents服务器
genagents_server = None
genagents_thread = None
monitor_thread = None
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VUE_DIST_DIR = os.path.join(PROJECT_ROOT, "fay-frontend", "dist")
VUE_ASSETS_DIR = os.path.join(VUE_DIST_DIR, "assets")

__app = Flask(__name__)
# 禁用 Flask 默认日志
__app.logger.disabled = True
log = logging.getLogger('werkzeug')
log.disabled = True
# 禁用请求日志中间件
__app.config['PROPAGATE_EXCEPTIONS'] = True

auth = HTTPBasicAuth()
CORS(__app, supports_credentials=True)
register_auth_routes(__app)
register_avatar_routes(__app)
register_dashboard_routes(__app)
register_digital_human_routes(__app)
register_tourism_recommendation_routes(__app)

def load_users():
    try:
        with open('verifier.json') as f:
            users = json.load(f)
        return users
    except Exception as e:
        print(f"Error loading users: {e}")
        return {}

users = load_users()

@auth.verify_password
def verify_password(username, password):
    if not users or config_util.start_mode == 'common':
        return True
    if username in users and users[username] == password:
        return username


def __get_template():
    try:
        import time as _time
        return render_template('index.html', cache_bust=str(int(_time.time())))
    except Exception as e:
        return f"Error rendering template: {e}", 500

def __get_vue_app(legacy_template='index.html'):
    index_file = os.path.join(VUE_DIST_DIR, 'index.html')
    if os.path.exists(index_file):
        return send_from_directory(VUE_DIST_DIR, 'index.html')
    if legacy_template == 'index.html':
        return __get_template()
    return render_template(legacy_template)

def __get_device_list():
    try:
        if config_util.start_mode == 'common':
            audio = pyaudio.PyAudio()
            device_list = []
            for i in range(audio.get_device_count()):
                devInfo = audio.get_device_info_by_index(i)
                if devInfo['hostApi'] == 0:
                    device_list.append(devInfo["name"])
            return list(set(device_list))
        else:
            return []
    except Exception as e:
        print(f"Error getting device list: {e}")
        return []

def _as_bool(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "y", "on")
    return False

def _build_llm_url(base_url: str) -> str:
    if not base_url:
        return ""
    url = base_url.rstrip("/")
    if url.endswith("/chat/completions"):
        return url
    if url.endswith("/v1"):
        return url + "/chat/completions"
    return url + "/v1/chat/completions"


def _build_models_url(base_url: str) -> str:
    if not base_url:
        return ""
    url = base_url.rstrip("/")
    if url.endswith("/chat/completions"):
        url = url[:-len("/chat/completions")]
    if url.endswith("/v1"):
        return url + "/models"
    return url + "/v1/models"


def _forbid_unless_self_or_admin(username):
    current = auth_service.current_user()
    if not current:
        return None
    if current.get('role') == 'admin':
        return None
    if username and current.get('username') == username:
        return None
    return jsonify({'error': '权限不足'}), 403


def _client_ip():
    return request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip()


def _log_admin_action(action, resource='', details=None):
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
        util.log(1, f'记录管理审计日志失败: {exc}')


def _push_web_cmd(command):
    try:
        web = wsa_server.get_web_instance()
        if web is not None:
            web.add_cmd(command)
    except Exception as exc:
        util.log(1, f'推送面板消息失败: {exc}')


def _session_user_record(user):
    return [user[0], user[1], user[7] if len(user) > 7 else '']


def _get_session_user(username=None):
    current = auth_service.current_user()
    if current and current.get('role') != 'admin':
        username = current.get('username')
    username = username or (current or {}).get('username') or 'User'
    user = member_db.new_instance().get_user_by_username(username, include_hash=False)
    return user


def _forbid_unless_session_owner(session_id, username=None):
    current = auth_service.current_user()
    if not current or current.get('role') == 'admin':
        return None
    if int(session_id or 0) == 0:
        return _forbid_unless_self_or_admin(username)
    session = content_db.new_instance().get_chat_session(session_id)
    if session and int(session.get('user_id') or 0) == int(current.get('uid') or 0):
        return None
    return jsonify({'error': '权限不足'}), 403


def _normalize_llm_proxy_role(role):
    role_value = str(role or "user").strip().lower()
    if role_value in ("system", "user", "assistant", "tool", "function", "developer"):
        return role_value
    return "user"


def _prepare_llm_proxy_messages(messages):
    if isinstance(messages, str):
        return [{"role": "user", "content": messages}]
    if not isinstance(messages, list):
        return []

    normalized = []
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        item = dict(msg)
        item["role"] = _normalize_llm_proxy_role(item.get("role"))
        if "content" not in item and item["role"] not in ("assistant",):
            item["content"] = ""
        normalized.append(item)
    return normalized


def _prepare_llm_proxy_payload(payload, model_name):
    proxy_payload = dict(payload) if isinstance(payload, dict) else {}
    proxy_payload["messages"] = _prepare_llm_proxy_messages(proxy_payload.get("messages", []))
    if model_name:
        proxy_payload["model"] = model_name
    return proxy_payload


def _build_llm_proxy_headers(api_key, stream_requested=False):
    headers = {
        "Content-Type": "application/json",
    }
    if stream_requested:
        headers["Accept"] = "text/event-stream"
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _build_proxy_response(resp):
    try:
        content_type = resp.headers.get("Content-Type", "application/json")
        if "charset=" not in content_type.lower():
            content_type = f"{content_type}; charset=utf-8"
        body = resp.content
    finally:
        resp.close()
    return Response(
        body,
        status=resp.status_code,
        content_type=content_type,
    )


def _build_streaming_proxy_response(resp):
    content_type = resp.headers.get("Content-Type", "text/event-stream")
    if "charset=" not in content_type.lower():
        content_type = f"{content_type}; charset=utf-8"

    def generate():
        try:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
        finally:
            resp.close()

    return Response(
        stream_with_context(generate()),
        status=resp.status_code,
        content_type=content_type,
    )


def _langsmith_proxy_enabled():
    if RunTree is None:
        return False
    api_key = os.getenv("LANGSMITH_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        return False
    return _as_bool(os.getenv("LANGSMITH_TRACING")) or _as_bool(os.getenv("LANGCHAIN_TRACING_V2"))


def _langsmith_project_name():
    return (os.getenv("LANGSMITH_PROJECT") or os.getenv("LANGCHAIN_PROJECT") or "").strip() or None


def _langsmith_wrap_outputs(payload):
    if isinstance(payload, dict):
        return payload
    return {"response": payload}


def _langsmith_preview_text(value, limit=12000):
    text = value if isinstance(value, str) else str(value)
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n...[truncated {len(text) - limit} chars]"


def _langsmith_parse_response(body, content_type):
    text = body.decode("utf-8", errors="replace") if isinstance(body, (bytes, bytearray)) else str(body)
    lowered = (content_type or "").lower()
    if "application/json" in lowered:
        try:
            return json.loads(text)
        except Exception:
            pass
    return {"raw_text": _langsmith_preview_text(text)}


def _start_langsmith_proxy_trace(llm_url, payload):
    if not _langsmith_proxy_enabled():
        return None
    try:
        root_run = RunTree(
            name="Fay LLM Proxy",
            run_type="chain",
            project_name=_langsmith_project_name(),
            inputs={
                "url": llm_url,
                "request": payload,
            },
        )
        root_run.post()
        child_run = root_run.create_child(
            name="Upstream Chat Completions",
            run_type="llm",
            inputs=payload,
        )
        child_run.post()
        return {"root": root_run, "child": child_run}
    except Exception as exc:
        util.log(2, f"LangSmith proxy tracing init failed: {exc}")
        return None


def _finish_langsmith_proxy_trace(trace_state, *, outputs=None, error=None):
    if not trace_state:
        return
    root_run = trace_state.get("root")
    child_run = trace_state.get("child")
    try:
        if child_run is not None:
            if error:
                child_run.end(error=str(error))
            else:
                child_run.end(outputs=_langsmith_wrap_outputs(outputs))
            child_run.patch()
    except Exception as exc:
        util.log(2, f"LangSmith child trace finalize failed: {exc}")
    try:
        if root_run is not None:
            if error:
                root_run.end(error=str(error))
            else:
                root_run.end(outputs=_langsmith_wrap_outputs(outputs))
            root_run.patch()
    except Exception as exc:
        util.log(2, f"LangSmith root trace finalize failed: {exc}")


def _build_streaming_proxy_response_with_trace(resp, trace_state):
    content_type = resp.headers.get("Content-Type", "text/event-stream")
    if "charset=" not in content_type.lower():
        content_type = f"{content_type}; charset=utf-8"

    def generate():
        captured = bytearray()
        truncated = False
        try:
            for chunk in resp.iter_content(chunk_size=8192):
                if not chunk:
                    continue
                if len(captured) < 524288:
                    remaining = 524288 - len(captured)
                    captured.extend(chunk[:remaining])
                    if len(chunk) > remaining:
                        truncated = True
                else:
                    truncated = True
                yield chunk
            outputs = {
                "status_code": resp.status_code,
                "stream": True,
                "content_type": content_type,
                "sse_preview": _langsmith_preview_text(captured.decode("utf-8", errors="replace")),
                "truncated": truncated,
            }
            _finish_langsmith_proxy_trace(trace_state, outputs=outputs)
        except Exception as exc:
            _finish_langsmith_proxy_trace(trace_state, error=exc)
            raise
        finally:
            resp.close()

    return Response(
        stream_with_context(generate()),
        status=resp.status_code,
        content_type=content_type,
    )


def _normalize_openai_content(content):
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if text is not None:
                    parts.append(str(text))
                    continue
                if "content" in item:
                    parts.append(_normalize_openai_content(item.get("content")))
                    continue
            parts.append(str(item))
        return "".join(parts)
    if isinstance(content, dict):
        if "text" in content:
            return _normalize_openai_content(content.get("text"))
        if "content" in content:
            return _normalize_openai_content(content.get("content"))
    return str(content)


def _build_langchain_messages(messages):
    normalized = []
    if isinstance(messages, str):
        normalized.append(HumanMessage(content=messages))
        return normalized
    if not isinstance(messages, list):
        return normalized
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        role = str(msg.get("role", "user")).strip().lower()
        content = _normalize_openai_content(msg.get("content"))
        if content is None:
            content = ""
        if role == "system":
            normalized.append(SystemMessage(content=content))
        elif role == "assistant":
            normalized.append(AIMessage(content=content))
        else:
            normalized.append(HumanMessage(content=content))
    return normalized


def _safe_text_from_chunk(chunk):
    if chunk is None:
        return ""
    value = getattr(chunk, "content", "")
    return _normalize_openai_content(value)

def _build_langchain_base_url(base_url: str) -> str:
    if not base_url:
        return ""
    url = base_url.rstrip("/")
    if url.endswith("/v1/chat/completions"):
        return url[:-len("/chat/completions")]
    if url.endswith("/chat/completions"):
        return url[:-len("/chat/completions")]
    return url

@__app.route('/api/submit', methods=['post'])
@auth_service.require_auth
@auth_service.require_role('admin')
def api_submit():
    data = request.values.get('data')
    if not data:
        return jsonify({'result': 'error', 'message': '未提供数据'})
    try:
        config_data = json.loads(data)
        if 'config' not in config_data:
            return jsonify({'result': 'error', 'message': '数据中缺少config'})

        config_util.load_config()
        existing_config = config_util.config

        def merge_configs(existing, new):
            for key, value in new.items():
                if isinstance(value, dict) and key in existing:
                    if isinstance(existing[key], dict):
                        merge_configs(existing[key], value)
                    else:
                        existing[key] = value
                else:
                    existing[key] = value

        merge_configs(existing_config, config_data['config'])

        digital_human_service.ensure_digital_humans_config(existing_config)
        digital_human_service.sync_active_human_from_attribute(existing_config)
        config_util.save_config_sections(existing_config, config_data['config'].keys())
        config_util.load_config(force_reload=True)  # 强制重新加载配置
        _log_admin_action('config_update', 'config.json', {'keys': sorted(config_data['config'].keys())})

        return jsonify({'result': 'successful'})
    except json.JSONDecodeError:
        return jsonify({'result': 'error', 'message': '无效的JSON数据'})
    except Exception as e:
        return jsonify({'result': 'error', 'message': f'保存配置时出错: {e}'}), 500
    



@__app.route('/api/get-data', methods=['post'])
@auth_service.require_auth
@auth_service.require_role('admin')
def api_get_data():
    # 获取配置和语音列表
    try:
        config_util.load_config()
        voice_list = tts_voice.get_voice_list()
        send_voice_list = []
        if config_util.tts_module == 'ali':
            voice_list = [
                {"id": "abin", "name": "阿斌"},
                {"id": "zhixiaobai", "name": "知小白"},
                {"id": "zhixiaoxia", "name": "知小夏"},
                {"id": "zhixiaomei", "name": "知小妹"},
                {"id": "zhigui", "name": "知柜"},
                {"id": "zhishuo", "name": "知硕"},
                {"id": "aixia", "name": "艾夏"},
                {"id": "zhifeng_emo", "name": "知锋_多情感"},
                {"id": "zhibing_emo", "name": "知冰_多情感"},
                {"id": "zhimiao_emo", "name": "知妙_多情感"},
                {"id": "zhimi_emo", "name": "知米_多情感"},
                {"id": "zhiyan_emo", "name": "知燕_多情感"},
                {"id": "zhibei_emo", "name": "知贝_多情感"},
                {"id": "zhitian_emo", "name": "知甜_多情感"},
                {"id": "xiaoyun", "name": "小云"},
                {"id": "xiaogang", "name": "小刚"},
                {"id": "ruoxi", "name": "若兮"},
                {"id": "siqi", "name": "思琪"},
                {"id": "sijia", "name": "思佳"},
                {"id": "sicheng", "name": "思诚"},
                {"id": "aiqi", "name": "艾琪"},
                {"id": "aijia", "name": "艾佳"},
                {"id": "aicheng", "name": "艾诚"},
                {"id": "aida", "name": "艾达"},
                {"id": "ninger", "name": "宁儿"},
                {"id": "ruilin", "name": "瑞琳"},
                {"id": "siyue", "name": "思悦"},
                {"id": "aiya", "name": "艾雅"},
                {"id": "aimei", "name": "艾美"},
                {"id": "aiyu", "name": "艾雨"},
                {"id": "aiyue", "name": "艾悦"},
                {"id": "aijing", "name": "艾婧"},
                {"id": "xiaomei", "name": "小美"},
                {"id": "aina", "name": "艾娜"},
                {"id": "yina", "name": "伊娜"},
                {"id": "sijing", "name": "思婧"},
                {"id": "sitong", "name": "思彤"},
                {"id": "xiaobei", "name": "小北"},
                {"id": "aitong", "name": "艾彤"},
                {"id": "aiwei", "name": "艾薇"},
                {"id": "aibao", "name": "艾宝"},
                {"id": "shanshan", "name": "姗姗"},
                {"id": "chuangirl", "name": "小玥"},
                {"id": "lydia", "name": "Lydia"},
                {"id": "aishuo", "name": "艾硕"},
                {"id": "qingqing", "name": "青青"},
                {"id": "cuijie", "name": "翠姐"},
                {"id": "xiaoze", "name": "小泽"},
                {"id": "zhimao", "name": "知猫"},
                {"id": "zhiyuan", "name": "知媛"},
                {"id": "zhiya", "name": "知雅"},
                {"id": "zhiyue", "name": "知悦"},
                {"id": "zhida", "name": "知达"},
                {"id": "zhistella", "name": "知莎"},
                {"id": "kelly", "name": "Kelly"},
                {"id": "jiajia", "name": "佳佳"},
                {"id": "taozi", "name": "桃子"},
                {"id": "guijie", "name": "柜姐"},
                {"id": "stella", "name": "Stella"},
                {"id": "stanley", "name": "Stanley"},
                {"id": "kenny", "name": "Kenny"},
                {"id": "rosa", "name": "Rosa"},
                {"id": "mashu", "name": "马树"},
                {"id": "xiaoxian", "name": "小仙"},
                {"id": "yuer", "name": "悦儿"},
                {"id": "maoxiaomei", "name": "猫小美"},
                {"id": "aifei", "name": "艾飞"},
                {"id": "yaqun", "name": "亚群"},
                {"id": "qiaowei", "name": "巧薇"},
                {"id": "dahu", "name": "大虎"},
                {"id": "ailun", "name": "艾伦"},
                {"id": "jielidou", "name": "杰力豆"},
                {"id": "laotie", "name": "老铁"},
                {"id": "laomei", "name": "老妹"},
                {"id": "aikan", "name": "艾侃"}
            ]
            send_voice_list = {"voiceList": voice_list}
            _push_web_cmd(send_voice_list)
        elif config_util.tts_module == 'volcano':
            voice_list = [
                {"id": "BV001_streaming", "name": "通用女声"},
                {"id": "BV002_streaming", "name": "通用男声"},
                {"id": "zh_male_jingqiangkanye_moon_bigtts", "name": "京腔侃爷/Harmony"},
                {"id": "zh_female_shuangkuaisisi_moon_bigtts", "name": "爽快思思/Skye"},
                {"id": "zh_male_wennuanahu_moon_bigtts", "name": "温暖阿虎/Alvin"},
                {"id": "zh_female_wanwanxiaohe_moon_bigtts", "name": "湾湾小何"}
            ]
            send_voice_list = {"voiceList": voice_list}
            _push_web_cmd(send_voice_list)
        elif config_util.tts_module == 'openai':
            # 只包含你的 TTS 服务实际支持的音色
            voice_list = [
                {"id": "zh-CN-XiaoxiaoNeural", "name": "晓晓（女声）"},
                {"id": "zh-CN-YunxiNeural", "name": "云溪（男声）"},
                {"id": "zh-CN-YunyangNeural", "name": "云阳（男声）"},
                {"id": "zh-CN-XiaoyiNeural", "name": "晓伊（女声）"},
                {"id": "zh-CN-YunjianNeural", "name": "云健（男声）"},
                {"id": "zh-CN-XiaoxuanNeural", "name": "晓萱（女声）"},
                {"id": "zh-CN-YunxiaNeural", "name": "云夏（女声）"}
            ]
            send_voice_list = {"voiceList": voice_list}
            _push_web_cmd(send_voice_list)

        else:
            voice_list = tts_voice.get_voice_list()
            send_voice_list = []
            for voice in voice_list:
                voice_data = voice.value
                send_voice_list.append({"id": voice_data['name'], "name": voice_data['name']})
            _push_web_cmd({"voiceList": send_voice_list})
            voice_list = send_voice_list
        _push_web_cmd({"deviceList": __get_device_list()})
        if fay_booter.is_running():
            _push_web_cmd({"liveState": 1})
        digital_human_service.ensure_digital_humans_config(config_util.config)
        return json.dumps({'config': config_util.config, 'voice_list': voice_list})
    except Exception as e:
        return jsonify({'result': 'error', 'message': f'获取数据时出错: {e}'}), 500

@__app.route('/api/start-live', methods=['post'])
@auth_service.require_auth
@auth_service.require_role('admin')
def api_start_live():
    # 启动
    try:
        fay_booter.start()
        gsleep(1)
        wsa_server.get_web_instance().add_cmd({"liveState": 1})
        _log_admin_action('service_start', 'live')
        return '{"result":"successful"}'
    except Exception as e:
        return jsonify({'result': 'error', 'message': f'启动时出错: {e}'}), 500

@__app.route('/api/stop-live', methods=['post'])
@auth_service.require_auth
@auth_service.require_role('admin')
def api_stop_live():
    # 停止
    try:
        fay_booter.stop()
        gsleep(1)
        wsa_server.get_web_instance().add_cmd({"liveState": 0})
        _log_admin_action('service_stop', 'live')
        return '{"result":"successful"}'
    except Exception as e:
        return jsonify({'result': 'error', 'message': f'停止时出错: {e}'}), 500

@__app.route('/api/chat-sessions', methods=['GET'])
@auth_service.require_auth
def api_list_chat_sessions():
    try:
        user = _get_session_user(request.args.get('username'))
        if not user:
            return jsonify({'list': []})
        forbidden = _forbid_unless_self_or_admin(user['username'])
        if forbidden:
            return forbidden
        sessions = content_db.new_instance().list_chat_sessions(user['username'], user['uid'])
        return jsonify({'list': sessions})
    except Exception as e:
        return jsonify({'list': [], 'message': f'获取会话列表时出错: {e}'}), 500


@__app.route('/api/chat-sessions', methods=['POST'])
@auth_service.require_auth
def api_create_chat_session():
    try:
        data = request.get_json(silent=True) or {}
        user = _get_session_user(data.get('username'))
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        forbidden = _forbid_unless_self_or_admin(user['username'])
        if forbidden:
            return forbidden
        title = str(data.get('title') or '新会话').strip() or '新会话'
        session = content_db.new_instance().create_chat_session(user['username'], user['uid'], title)
        return jsonify({'success': True, 'session': session})
    except Exception as e:
        return jsonify({'error': f'创建会话时出错: {e}'}), 500


@__app.route('/api/chat-sessions/<int:session_id>', methods=['PUT'])
@auth_service.require_auth
def api_rename_chat_session(session_id):
    try:
        data = request.get_json(silent=True) or {}
        title = str(data.get('title') or '').strip()
        if not title:
            return jsonify({'error': '会话名称不能为空'}), 400
        session = content_db.new_instance().get_chat_session(session_id)
        if not session:
            return jsonify({'error': '会话不存在'}), 404
        forbidden = _forbid_unless_session_owner(session_id, session.get('username'))
        if forbidden:
            return forbidden
        session = content_db.new_instance().rename_chat_session(session_id, title)
        return jsonify({'success': True, 'session': session})
    except Exception as e:
        return jsonify({'error': f'重命名会话时出错: {e}'}), 500


@__app.route('/api/chat-sessions/<int:session_id>', methods=['DELETE'])
@auth_service.require_auth
def api_delete_chat_session(session_id):
    try:
        if session_id == 0:
            user = _get_session_user(request.args.get('username'))
            if not user:
                return jsonify({'error': '用户不存在'}), 404
            forbidden = _forbid_unless_self_or_admin(user['username'])
            if forbidden:
                return forbidden
            deleted = content_db.new_instance().delete_chat_session(0, user['username'], user['uid'])
            return jsonify({'success': True, 'deleted_messages': deleted})

        session = content_db.new_instance().get_chat_session(session_id)
        if not session:
            return jsonify({'error': '会话不存在'}), 404
        forbidden = _forbid_unless_session_owner(session_id, session.get('username'))
        if forbidden:
            return forbidden
        deleted = content_db.new_instance().delete_chat_session(session_id)
        return jsonify({'success': True, 'deleted_messages': deleted})
    except Exception as e:
        return jsonify({'error': f'删除会话时出错: {e}'}), 500


@__app.route('/api/send', methods=['post'])
@auth_service.require_auth
def api_send():
    # 接收前端发送的消息
    data = request.values.get('data')
    if not data:
        return jsonify({'result': 'error', 'message': '未提供数据'})
    try:
        info = json.loads(data)
        username = info.get('username')
        msg = info.get('msg')
        session_id = info.get('session_id')
        if not username or not msg:
            return jsonify({'result': 'error', 'message': '用户名和消息内容不能为空'})
        forbidden = _forbid_unless_self_or_admin(username)
        if forbidden:
            return forbidden
        if session_id is not None:
            forbidden = _forbid_unless_session_owner(session_id, username)
            if forbidden:
                return forbidden
        msg = msg.strip()

        interact = Interact("text", 1, {'user': username, 'msg': msg, 'session_id': session_id})
        util.printInfo(1, username, '[文字发送按钮]{}'.format(interact.data["msg"]), time.time())
        fay_booter.feiFei.on_interact(interact)
        return '{"result":"successful"}'
    except json.JSONDecodeError:
        return jsonify({'result': 'error', 'message': '无效的JSON数据'})
    except Exception as e:
        return jsonify({'result': 'error', 'message': f'发送消息时出错: {e}'}), 500

# 获取指定用户的消息记录（支持分页）
@__app.route('/api/get-msg', methods=['post'])
@auth_service.require_auth
def api_get_Msg():
    try:
        data = request.form.get('data')
        if data is None:
            data = request.get_json(silent=True) or {}
        else:
            data = json.loads(data)
        if not isinstance(data, dict):
            data = {}
        username = data.get("username")
        session_id = data.get("session_id")
        limit = data.get("limit", 30)  # 默认每页30条
        offset = data.get("offset", 0)  # 默认从0开始
        forbidden = _forbid_unless_self_or_admin(username)
        if forbidden:
            return forbidden
        if session_id is not None:
            forbidden = _forbid_unless_session_owner(session_id, username)
            if forbidden:
                return forbidden
        contentdb = content_db.new_instance()
        uid = 0
        if username:
            uid = member_db.new_instance().find_user(username)
            if uid == 0:
                return json.dumps({'list': [], 'total': 0, 'hasMore': False})
        # 获取总数用于判断是否还有更多
        total = contentdb.get_message_count(uid, session_id=session_id)
        list = contentdb.get_list('all', 'desc', limit, uid, offset, session_id=session_id)
        relist = []
        i = len(list) - 1
        while i >= 0:
            timezone = pytz.timezone('Asia/Shanghai')
            ts = list[i][3]
            ts_sec = ts / 1000 if ts > 9999999999 else ts  # 兼容旧秒级和新毫秒级时间戳
            timetext = datetime.datetime.fromtimestamp(ts_sec, timezone).strftime('%Y-%m-%d %H:%M:%S.') + f"{int(ts % 1000) if ts > 9999999999 else 0:03d}"
            image_urls = []
            if len(list[i]) > 8 and list[i][8]:
                try:
                    image_urls = json.loads(list[i][8])
                except Exception:
                    image_urls = []
            relist.append(dict(
                type=list[i][0],
                way=list[i][1],
                content=list[i][2],
                createtime=list[i][3],
                timetext=timetext,
                username=list[i][5],
                id=list[i][6],
                is_adopted=list[i][7],
                images=image_urls,
                session_id=list[i][9] if len(list[i]) > 9 and list[i][9] is not None else 0,
            ))
            i -= 1
        if fay_booter.is_running():
            wsa_server.get_web_instance().add_cmd({"liveState": 1})
        hasMore = (offset + len(list)) < total
        return json.dumps({'list': relist, 'total': total, 'hasMore': hasMore})
    except json.JSONDecodeError:
        return jsonify({'list': [], 'total': 0, 'hasMore': False, 'message': '无效的JSON数据'})
    except Exception as e:
        return jsonify({'list': [], 'total': 0, 'hasMore': False, 'message': f'获取消息时出错: {e}'}), 500

# 根据ID获取单条消息
@__app.route('/api/get-msg-by-id', methods=['post'])
@auth_service.require_auth
def api_get_msg_by_id():
    try:
        data = request.get_json(silent=True) or {}
        msg_id = data.get('id')
        if not msg_id:
            return jsonify({'content': ''})
        record = content_db.new_instance().get_content_by_id(msg_id)
        if record:
            forbidden = _forbid_unless_self_or_admin(record[5])
            if forbidden:
                return forbidden
            return jsonify({'content': record[3]})
        return jsonify({'content': ''})
    except Exception as e:
        return jsonify({'content': '', 'error': str(e)})

#模型列表接口
def _extract_context_length(model_obj):
    """从上游模型对象中提取上下文长度（兼容多种服务实现）"""
    for key in ("context_length", "max_model_len", "context_window", "max_context_length"):
        val = model_obj.get(key)
        if val is not None:
            try:
                return int(val)
            except (ValueError, TypeError):
                pass
    return None


def _fetch_upstream_models():
    """获取上游模型列表，尝试提取 context_length"""
    config_util.load_config()
    api_key = config_util.key_gpt_api_key
    models_url = _build_models_url(config_util.gpt_base_url)
    if not models_url:
        return [], None

    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    resp = requests.get(models_url, headers=headers, timeout=10)
    if resp.status_code != 200:
        return [], None

    result = resp.json()
    data = result.get("data") if isinstance(result, dict) else None
    if not isinstance(data, list):
        return [], None

    # 找到当前配置的模型，提取其 context_length
    current_model = getattr(config_util, "gpt_model_engine", None)
    current_ctx = None
    for m in data:
        if not isinstance(m, dict):
            continue
        ctx = _extract_context_length(m)
        if ctx is not None and m.get("id") == current_model:
            current_ctx = ctx

    # 如果列表里没有 context_length，尝试查询单个模型详情
    if current_ctx is None and current_model:
        try:
            base = models_url.rstrip("/")
            detail_resp = requests.get(
                f"{base}/{current_model}",
                headers=headers,
                timeout=10,
            )
            if detail_resp.status_code == 200:
                detail = detail_resp.json()
                if isinstance(detail, dict):
                    current_ctx = _extract_context_length(detail)
        except Exception:
            pass

    return data, current_ctx


@__app.route('/v1/models', methods=['get'])
@__app.route('/api/send/v1/models', methods=['get'])
def api_v1_models():
    upstream_models = []
    fay_context_length = None
    try:
        upstream_models, fay_context_length = _fetch_upstream_models()
    except Exception:
        pass

    fay_model_base = {
        "object": "model",
        "created": 0,
        "owned_by": "fay",
    }
    fay_models = []
    for model_id in ("fay", "fay-streaming", "llm"):
        entry = dict(fay_model_base, id=model_id)
        if fay_context_length is not None:
            entry["context_length"] = fay_context_length
        fay_models.append(entry)

    return jsonify({
        "object": "list",
        "data": fay_models + upstream_models,
    })


#文字沟通接口
@__app.route('/v1/chat/completions', methods=['post'])
@__app.route('/api/send/v1/chat/completions', methods=['post'])
@auth_service.require_auth
def api_send_v1_chat_completions():
    # 处理聊天完成请求
    data = request.get_json()
    if not data:
        return jsonify({'error': 'missing request body'})
    try:
        model = data.get('model', 'fay')
        if model not in ('fay', 'fay-streaming'):
            try:
                config_util.load_config()
                api_key = config_util.key_gpt_api_key
                llm_url = _build_llm_url(config_util.gpt_base_url)
            except Exception as exc:
                return jsonify({'error': f'LLM config load failed: {exc}'}), 500

            if not llm_url:
                return jsonify({'error': 'LLM base_url is not configured'}), 500

            stream_requested = _as_bool(data.get('stream', False))
            # model=llm 时自动使用 system.conf 中配置的模型
            model_name = config_util.gpt_model_engine if model == 'llm' else model
            payload = _prepare_llm_proxy_payload(data, model_name)
            if not payload.get("messages"):
                return jsonify({'error': 'messages is required'}), 400

            headers = _build_llm_proxy_headers(api_key, stream_requested=stream_requested)
            trace_state = _start_langsmith_proxy_trace(llm_url, payload)

            try:
                if stream_requested:
                    resp = requests.post(llm_url, headers=headers, json=payload, stream=True, timeout=(10, 600))
                    content_type = resp.headers.get("Content-Type", "")
                    if "text/event-stream" not in content_type.lower():
                        body = resp.content
                        outputs = {
                            "status_code": resp.status_code,
                            "stream": False,
                            "content_type": content_type,
                            "response": _langsmith_parse_response(body, content_type),
                        }
                        if resp.status_code >= 400:
                            _finish_langsmith_proxy_trace(trace_state, error=f"HTTP {resp.status_code}: {_langsmith_preview_text(outputs['response'])}")
                        else:
                            _finish_langsmith_proxy_trace(trace_state, outputs=outputs)
                        return _build_proxy_response(resp)
                    return _build_streaming_proxy_response_with_trace(resp, trace_state)

                resp = requests.post(llm_url, headers=headers, json=payload, timeout=600)
                body = resp.content
                content_type = resp.headers.get("Content-Type", "application/json")
                outputs = {
                    "status_code": resp.status_code,
                    "stream": False,
                    "content_type": content_type,
                    "response": _langsmith_parse_response(body, content_type),
                }
                if resp.status_code >= 400:
                    _finish_langsmith_proxy_trace(trace_state, error=f"HTTP {resp.status_code}: {_langsmith_preview_text(outputs['response'])}")
                else:
                    _finish_langsmith_proxy_trace(trace_state, outputs=outputs)
                return _build_proxy_response(resp)
            except Exception as exc:
                _finish_langsmith_proxy_trace(trace_state, error=exc)
                return jsonify({'error': f'LLM request failed: {exc}'}), 500

        last_content = ""
        username = (data.get("user") or "").strip()
        if not username:
            auth_header = (request.headers.get("Authorization") or "").strip()
            if auth_header.startswith("Bearer "):
                username = auth_header[7:].strip()
        username = username or "User"
        current = auth_service.current_user()
        if current and current.get('role') != 'admin':
            username = current.get('username') or username
        session_id = data.get('session_id')
        forbidden = _forbid_unless_self_or_admin(username)
        if forbidden:
            return forbidden
        if session_id is not None:
            forbidden = _forbid_unless_session_owner(session_id, username)
            if forbidden:
                return forbidden

        # 解析 messages，支持多模态内容
        messages = data.get("messages")
        image_urls = []  # 图片URL列表

        if isinstance(messages, list) and messages:
            last_message = messages[-1] or {}
            content = last_message.get("content")

            # 支持 OpenAI 多模态格式
            if isinstance(content, list):
                # content 是数组，包含 text 和 image_url
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text":
                            last_content = item.get("text", "")
                        elif item.get("type") == "image_url":
                            img_url = item.get("image_url", {}).get("url", "")
                            if img_url:
                                image_urls.append(img_url)
            elif isinstance(content, str):
                # content 是字符串，纯文本消息
                last_content = content
            else:
                last_content = str(content) if content else ""
        elif isinstance(messages, str):
            last_content = messages

        observation = data.get('observation', '')
        # 检查请求中是否指定了流式传输
        stream_requested = data.get('stream', False)
        no_reply = _as_bool(data.get('no_reply', data.get('noReply', False)))
        obs_text = ""
        if observation is not None:
            obs_text = observation.strip() if isinstance(observation, str) else str(observation).strip()
        message_text = last_content.strip() if isinstance(last_content, str) else str(last_content).strip()

        # 修改验证逻辑：允许纯图片消息（没有文字但有图片）
        if not message_text and not obs_text and not image_urls:
            return jsonify({'error': 'messages and observation are both empty'}), 400

        # 如果只有图片没有文字，添加默认提示词
        if not message_text and image_urls:
            message_text = "[图片]"
            last_content = "[图片]"  # 也更新 last_content

        if not message_text and obs_text:
            no_reply = True
        if no_reply:
            interact = Interact("text", 1, {
                'user': username,
                'msg': last_content,
                'images': image_urls,  # 新增：图片列表
                'observation': str(observation),
                'stream': bool(stream_requested),
                'no_reply': True,
                'session_id': session_id
            })
            util.printInfo(1, username, '[text chat no_reply]{}'.format(interact.data["msg"]), time.time())
            fay_booter.feiFei.on_interact(interact)
            if stream_requested or model == 'fay-streaming':
                def generate():
                    message = {
                        "id": "faystreaming-" + str(uuid.uuid4()),
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": model,
                        "choices": [
                            {
                                "delta": {
                                    "content": ""
                                },
                                "index": 0,
                                "finish_reason": "stop"
                            }
                        ],
                        "usage": {
                            "prompt_tokens": len(last_content),
                            "completion_tokens": 0,
                            "total_tokens": len(last_content)
                        },
                        "system_fingerprint": "",
                        "no_reply": True
                    }
                    yield f"data: {json.dumps(message)}\n\n"
                    yield 'data: [DONE]\n\n'
                return Response(generate(), mimetype='text/event-stream')
            return jsonify({
                "id": "fay-" + str(uuid.uuid4()),
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": ""
                        },
                        "logprobs": "",
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": len(last_content),
                    "completion_tokens": 0,
                    "total_tokens": len(last_content)
                },
                "system_fingerprint": "",
                "no_reply": True
            })
        if stream_requested or model == 'fay-streaming':
            interact = Interact("text", 1, {
                'user': username,
                'msg': last_content,
                'images': image_urls,  # 新增：图片列表
                'observation': str(observation),
                'stream': True,
                'session_id': session_id
            })
            util.printInfo(1, username, '[文字沟通接口(流式)]{}'.format(interact.data["msg"]), time.time())
            fay_booter.feiFei.on_interact(interact)
            return gpt_stream_response(last_content, username)
        else:
            interact = Interact("text", 1, {
                'user': username,
                'msg': last_content,
                'images': image_urls,  # 新增：图片列表
                'observation': str(observation),
                'stream': False,
                'session_id': session_id
            })
            util.printInfo(1, username, '[文字沟通接口(非流式)]{}'.format(interact.data["msg"]), time.time())
            fay_booter.feiFei.on_interact(interact)
            return non_streaming_response(last_content, username)
    except Exception as e:
        return jsonify({'error': f'处理请求时出错: {e}'}), 500

@__app.route('/api/get-member-list', methods=['post'])
@auth_service.require_auth
def api_get_Member_list():
    # 获取成员列表
    try:
        memberdb = member_db.new_instance()
        list = memberdb.get_all_users()
        current = auth_service.current_user()
        if current and current.get('role') != 'admin':
            list = [user for user in list if user[1] == current.get('username')]
        return jsonify({'list': [_session_user_record(user) for user in list]})
    except Exception as e:
        return jsonify({'list': [], 'message': f'获取成员列表时出错: {e}'}), 500
@__app.route('/api/add-user', methods=['POST'])
@auth_service.require_auth
@auth_service.require_role('admin')
def api_add_user():
    """添加新用户"""
    try:
        data = request.get_json()
        if not data or 'username' not in data:
            return jsonify({'success': False, 'message': '缺少用户名参数'}), 400

        username = data['username'].strip()

        if not username:
            return jsonify({'success': False, 'message': '用户名不能为空'}), 400

        if username == 'User':
            return jsonify({'success': False, 'message': '不能使用保留的用户名 "User"'}), 400

        # 检查用户是否已存在
        memberdb = member_db.new_instance()
        if memberdb.is_username_exist(username) != "notexists":
            return jsonify({'success': False, 'message': '该用户名已存在'}), 400

        # 添加用户
        result = memberdb.add_user(username)
        if result == "success":
            # 获取新用户的 uid
            uid = memberdb.find_user(username)
            return jsonify({
                'success': True,
                'message': f'用户 {username} 已添加',
                'uid': uid
            })
        else:
            return jsonify({'success': False, 'message': result}), 400

    except Exception as e:
        return jsonify({'success': False, 'message': f'添加用户时出错: {e}'}), 500

@__app.route('/api/get-run-status', methods=['post'])
def api_get_run_status():
    # 获取运行状态
    try:
        status = fay_booter.is_running()
        return json.dumps({'status': status})
    except Exception as e:
        return jsonify({'status': False, 'message': f'获取运行状态时出错: {e}'}), 500

@__app.route('/api/delete-user', methods=['POST'])
@auth_service.require_auth
@auth_service.require_role('admin')
def api_delete_user():
    """删除用户及其所有数据（聊天记录、记忆文件）"""
    try:
        data = request.get_json()
        if not data or 'username' not in data:
            return jsonify({'success': False, 'message': '缺少用户名参数'}), 400

        username = data['username']

        # 不允许删除主人账户
        if username == 'User':
            return jsonify({'success': False, 'message': '无法删除主人账户'}), 400

        deleted_msgs = 0
        deleted_memory = False
        deleted_user = False

        # 1. 删除聊天记录（fay.db 中的 T_Msg 和 T_Adopted）
        try:
            deleted_msgs = content_db.new_instance().delete_messages_by_username(username)
        except Exception as e:
            print(f"删除聊天记录时出错: {e}")

        # 2. 删除用户记忆文件目录（如果启用了按用户隔离）
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            mem_base = os.path.join(base_dir, "memory")
            user_memory_dir = os.path.join(mem_base, str(username))

            if os.path.exists(user_memory_dir) and os.path.isdir(user_memory_dir):
                import shutil
                shutil.rmtree(user_memory_dir)
                deleted_memory = True
                print(f"已删除用户记忆目录: {user_memory_dir}")

            # 清除缓存的 agent 对象
            try:
                if hasattr(nlp_cognitive_stream, 'agents') and username in nlp_cognitive_stream.agents:
                    del nlp_cognitive_stream.agents[username]
            except Exception:
                pass
        except Exception as e:
            print(f"删除记忆文件时出错: {e}")

        # 3. 从用户表删除用户
        try:
            member_db.new_instance().delete_user(username)
            deleted_user = True
        except Exception as e:
            print(f"删除用户记录时出错: {e}")

        return jsonify({
            'success': True,
            'message': f'用户 {username} 已删除',
            'details': {
                'deleted_messages': deleted_msgs,
                'deleted_memory': deleted_memory,
                'deleted_user': deleted_user
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'删除用户时出错: {e}'}), 500

@__app.route('/api/get-user-extra-info', methods=['POST'])
@auth_service.require_auth
def api_get_user_extra_info():
    """获取用户补充信息"""
    try:
        data = request.get_json()
        if not data or 'username' not in data:
            return jsonify({'success': False, 'message': '缺少用户名参数'}), 400

        username = data['username']
        forbidden = _forbid_unless_self_or_admin(username)
        if forbidden:
            return forbidden
        extra_info = member_db.new_instance().get_extra_info(username)
        return jsonify({'success': True, 'extra_info': extra_info})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取补充信息时出错: {e}'}), 500

@__app.route('/api/update-user-extra-info', methods=['POST'])
@auth_service.require_auth
def api_update_user_extra_info():
    """更新用户补充信息"""
    try:
        data = request.get_json()
        if not data or 'username' not in data:
            return jsonify({'success': False, 'message': '缺少用户名参数'}), 400

        username = data['username']
        forbidden = _forbid_unless_self_or_admin(username)
        if forbidden:
            return forbidden
        extra_info = data.get('extra_info', '')
        member_db.new_instance().update_extra_info(username, extra_info)
        return jsonify({'success': True, 'message': '补充信息已更新'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新补充信息时出错: {e}'}), 500

@__app.route('/api/get-user-portrait', methods=['POST'])
@auth_service.require_auth
def api_get_user_portrait():
    """获取用户画像"""
    try:
        data = request.get_json()
        if not data or 'username' not in data:
            return jsonify({'success': False, 'message': '缺少用户名参数'}), 400

        username = data['username']
        forbidden = _forbid_unless_self_or_admin(username)
        if forbidden:
            return forbidden
        user_portrait = member_db.new_instance().get_user_portrait(username)
        return jsonify({'success': True, 'user_portrait': user_portrait})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取用户画像时出错: {e}'}), 500

@__app.route('/api/update-user-portrait', methods=['POST'])
@auth_service.require_auth
def api_update_user_portrait():
    """更新用户画像"""
    try:
        data = request.get_json()
        if not data or 'username' not in data:
            return jsonify({'success': False, 'message': '缺少用户名参数'}), 400

        username = data['username']
        forbidden = _forbid_unless_self_or_admin(username)
        if forbidden:
            return forbidden
        user_portrait = data.get('user_portrait', '')
        member_db.new_instance().update_user_portrait(username, user_portrait)
        return jsonify({'success': True, 'message': '用户画像已更新'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新用户画像时出错: {e}'}), 500

@__app.route('/api/get-system-status', methods=['get'])
def api_get_system_status():
    # 获���系统各组件连接状态
    try:
        username = request.args.get('username')
        server_status = True
        
        # 数字人状态 (HumanServer 10002)
        # 检查指定用户是否连接了数字人端
        digital_human_status = False
        try:
            wsa_instance = wsa_server.get_instance()
            if wsa_instance and username:
                digital_human_status = wsa_instance.is_connected(username)
        except Exception:
            digital_human_status = False
        
        # 远程音频状态 (Socket 10001)
        # 检查指定用户是否连接了远程音频
        remote_audio_status = False
        try:
            if username and hasattr(fay_booter, 'DeviceInputListenerDict'):
                for listener in fay_booter.DeviceInputListenerDict.values():
                    if listener.username == username:
                        remote_audio_status = True
                        break
        except Exception:
            remote_audio_status = False
            
        return jsonify({
            'server': server_status,
            'digital_human': digital_human_status,
            'remote_audio': remote_audio_status
        })
    except Exception as e:
        return jsonify({'server': False, 'digital_human': False, 'remote_audio': False, 'error': str(e)}), 500

@__app.route('/api/get-audio-config', methods=['GET'])
def api_get_audio_config():
    """获取麦克风和扬声器的配置状态"""
    try:
        mic_enabled = config_util.config.get('source', {}).get('record', {}).get('enabled', False)
        speaker_enabled = config_util.config.get('interact', {}).get('playSound', False)

        return jsonify({
            'mic': mic_enabled,
            'speaker': speaker_enabled
        })
    except Exception as e:
        return jsonify({'mic': False, 'speaker': False, 'error': str(e)}), 500

@__app.route('/api/adopt-msg', methods=['POST'])
@auth_service.require_auth
@auth_service.require_role('admin')
def adopt_msg():
    # 采纳消息
    data = request.get_json()
    if not data:
        return jsonify({'status':'error', 'msg': '未提供数据'})

    id = data.get('id')

    if not id:
        return jsonify({'status':'error', 'msg': 'id不能为空'})

    if  config_util.config["interact"]["QnA"] == "":
        return jsonify({'status':'error', 'msg': '请先设置Q&A文件'})

    try:
        info = content_db.new_instance().get_content_by_id(id)
        content = info[3] if info else ''
        if info is not None:
            # 过滤掉 think 标签及其内容
            content = re.sub(r'<think>[\s\S]*?</think>', '', content, flags=re.IGNORECASE).strip()
            previous_info = content_db.new_instance().get_previous_user_message(id)
            previous_content = previous_info[3] if previous_info else ''
            result = content_db.new_instance().adopted_message(id)
            if result:
                qa_service.QAService().record_qapair(previous_content, content)
                return jsonify({'status': 'success', 'msg': '采纳成功'})
            else:
                return jsonify({'status':'error', 'msg': '采纳失败'}), 500
        else:
            return jsonify({'status':'error', 'msg': '消息未找到'}), 404
    except Exception as e:
        return jsonify({'status':'error', 'msg': f'采纳消息时出错: {e}'}), 500

@__app.route('/api/unadopt-msg', methods=['POST'])
@auth_service.require_auth
@auth_service.require_role('admin')
def unadopt_msg():
    # 取消采纳消息
    data = request.get_json()
    if not data:
        return jsonify({'status':'error', 'msg': '未提供数据'})

    id = data.get('id')

    if not id:
        return jsonify({'status':'error', 'msg': 'id不能为空'})

    try:
        info = content_db.new_instance().get_content_by_id(id)
        if info is None:
            return jsonify({'status':'error', 'msg': '消息未找到'}), 404

        content = info[3]
        # 过滤掉 think 标签及其内容，用于匹配 QA 文件中的答案
        clean_content = re.sub(r'<think>[\s\S]*?</think>', '', content, flags=re.IGNORECASE).strip()

        # 从数据库中删除采纳记录，并获取所有相同内容的消息ID
        success, same_content_ids = content_db.new_instance().unadopt_message(id, clean_content)

        if success:
            # 从 QA 文件中删除对应记录
            qa_service.QAService().remove_qapair(clean_content)
            return jsonify({
                'status': 'success',
                'msg': '取消采纳成功',
                'unadopted_ids': same_content_ids
            })
        else:
            return jsonify({'status':'error', 'msg': '取消采纳失败'}), 500
    except Exception as e:
        return jsonify({'status':'error', 'msg': f'取消采纳时出错: {e}'}), 500

def gpt_stream_response(last_content, username):
    sm = stream_manager.new_instance()
    _, nlp_Stream = sm.get_Stream(username)
    def generate():
        conversation_id = sm.get_conversation_id(username)
        while True:
            sentence = nlp_Stream.read()
            if sentence is None:
                gsleep(0.01)
                continue

            # 跳过非当前会话
            try:
                m = re.search(r"__<cid=([^>]+)>__", sentence)
                producer_cid = m.group(1)
                if producer_cid != conversation_id:
                    continue
                if m:
                    sentence = sentence.replace(m.group(0), "")
            except Exception as e:
                print(e)
            is_first = "_<isfirst>" in sentence
            is_end = "_<isend>" in sentence
            content = sentence.replace("_<isfirst>", "").replace("_<isend>", "").replace("_<isqa>", "")
            # 移除 prestart 标签及其内容，不返回给API调用方
            content = re.sub(r'<prestart>[\s\S]*?</prestart>', '', content, flags=re.IGNORECASE)
            if content or is_first or is_end:  # 只有当有实际内容时才发送
                message = {
                    "id": "faystreaming-" + str(uuid.uuid4()),
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": "fay-streaming",
                    "choices": [
                        {
                            "delta": {
                                "content": content
                            },
                            "index": 0,
                            "finish_reason": "stop" if is_end else None
                        }
                    ],
                    #TODO 这里的token计算方式需要优化
                    "usage": {
                        "prompt_tokens": len(last_content) if is_first else 0,
                        "completion_tokens": len(content),
                        "total_tokens": len(last_content) + len(content)
                    },
                    "system_fingerprint": ""
                }
                yield f"data: {json.dumps(message)}\n\n"
            if is_end:
                break
            gsleep(0.01)
        yield 'data: [DONE]\n\n'

    return Response(generate(), mimetype='text/event-stream')

# 处理非流式响应
@__app.route('/v1/embeddings', methods=['post'])
@__app.route('/api/send/v1/embeddings', methods=['post'])
def api_send_v1_embeddings():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'missing request body'})
    try:
        from utils.api_embedding_service import build_openai_embedding_response
        result = build_openai_embedding_response(data)
        return jsonify(result)
    except Exception as exc:
        return jsonify({'error': f'Embedding request failed: {exc}'}), 500


def non_streaming_response(last_content, username):
    sm = stream_manager.new_instance()
    _, nlp_Stream = sm.get_Stream(username)
    text = ""
    conversation_id = sm.get_conversation_id(username)
    while True:
        sentence = nlp_Stream.read()
        if sentence is None:
            gsleep(0.01)
            continue

        # 跳过非当前会话
        try:
            m = re.search(r"__<cid=([^>]+)>__", sentence)
            producer_cid = m.group(1)
            if producer_cid != conversation_id:
                continue
            if m:
                sentence = sentence.replace(m.group(0), "")
        except Exception as e:
            print(e)
        is_first = "_<isfirst>" in sentence
        is_end = "_<isend>" in sentence
        text += sentence.replace("_<isfirst>", "").replace("_<isend>", "").replace("_<isqa>", "")
        if is_end:
            break
    # 移除 prestart 标签及其内容，不返回给API调用方
    text = re.sub(r'<prestart>[\s\S]*?</prestart>', '', text, flags=re.IGNORECASE)
    return jsonify({
        "id": "fay-" + str(uuid.uuid4()),
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "fay",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": text
                },
                "logprobs": "",
                "finish_reason": "stop"
            }
        ],
        #TODO 这里的token计算方式需要优化
        "usage": {
            "prompt_tokens": len(last_content),
            "completion_tokens": len(text),
            "total_tokens": len(last_content) + len(text)
        },
        "system_fingerprint": ""
    })

@__app.route('/', methods=['get'])
@auth.login_required
def home_get():
    try:
        return __get_vue_app()
    except Exception as e:
        return f"Error loading home page: {e}", 500

@__app.route('/', methods=['post'])
@auth.login_required
def home_post():
    try:
        return __get_vue_app()
    except Exception as e:
        return f"Error processing request: {e}", 500

@__app.route('/setting', methods=['get'])
def setting():
    try:
        return __get_vue_app('setting.html')
    except Exception as e:
        return f"Error loading settings page: {e}", 500

@__app.route('/live2d', methods=['get'])
def live2d():
    try:
        return __get_vue_app()
    except Exception as e:
        return f"Error loading Live2D page: {e}", 500

@__app.route('/dashboard', methods=['get'])
def dashboard():
    try:
        return __get_vue_app()
    except Exception as e:
        return f"Error loading dashboard page: {e}", 500

@__app.route('/visitor-report', methods=['get'])
def visitor_report():
    try:
        return __get_vue_app()
    except Exception as e:
        return f"Error loading visitor report page: {e}", 500

@__app.route('/knowledge', methods=['get'])
def knowledge():
    try:
        return __get_vue_app()
    except Exception as e:
        return f"Error loading knowledge page: {e}", 500

@__app.route('/mcp', methods=['get'])
def mcp():
    try:
        return __get_vue_app()
    except Exception as e:
        return f"Error loading MCP page: {e}", 500

@__app.route('/assets/<path:filename>', methods=['get'])
def vue_assets(filename):
    if os.path.exists(os.path.join(VUE_ASSETS_DIR, filename)):
        return send_from_directory(VUE_ASSETS_DIR, filename)
    return jsonify({'error': '资源未找到'}), 404

@__app.route('/Page3', methods=['get'])
def Page3():
    try:
        return render_template('Page3.html')
    except Exception as e:
        return f"Error loading settings page: {e}", 500


# 输出的音频http
@__app.route('/audio/<filename>')
def serve_audio(filename):
    audio_file = os.path.join(os.getcwd(), "samples", filename)
    if os.path.exists(audio_file):
        return send_file(audio_file)
    else:
        return jsonify({'error': '文件未找到'}), 404

# 输出的表情gif
@__app.route('/robot/<filename>')
def serve_gif(filename):
    gif_file = os.path.join(os.getcwd(), "gui", "robot", filename)
    if os.path.exists(gif_file):
        return send_file(gif_file)
    else:
        return jsonify({'error': '文件未找到'}), 404

#打招呼
@__app.route('/to-greet', methods=['POST'])
def to_greet():
    data = request.get_json()
    username = data.get('username', 'User')
    observation = data.get('observation', '')
    interact = Interact("hello", 1, {'user': username, 'msg': '按观测要求打个招呼', 'observation': str(observation)})
    text = fay_booter.feiFei.on_interact(interact)
    return jsonify({'status': 'success', 'data': text, 'msg': '已进行打招呼'}), 200 

#唤醒:在普通唤醒模式，进行大屏交互才有意义
@__app.route('/to-wake', methods=['POST'])
def to_wake():
    data = request.get_json()
    username = data.get('username', 'User')
    observation = data.get('observation', '')
    fay_booter.recorderListener.wakeup_matched = True
    return jsonify({'status': 'success', 'msg': '已唤醒'}), 200 

#打断
@__app.route('/to-stop-talking', methods=['POST'])
def to_stop_talking():
    try:
        data = request.get_json()
        username = data.get('username', 'User')
        stream_manager.new_instance().clear_Stream_with_audio(username)

        result = "interrupted"  # 简单的结果标识
        return jsonify({
            'status': 'success',
            'data': str(result) if result is not None else '',
            'msg': f'已停止用户 {username} 的说话'
        }), 200
    except Exception as e:
        username_str = username if 'username' in locals() else 'Unknown'
        util.printInfo(1, username_str, f"打断操作失败: {str(e)}")
        return jsonify({
            'status': 'error',
            'msg': str(e)
        }), 500

#麦克风开关
@__app.route('/api/toggle-microphone', methods=['POST'])
@auth_service.require_auth
@auth_service.require_role('admin')
def api_toggle_microphone():
    try:
        data = request.get_json()
        if data and 'enabled' in data:
            enabled = data['enabled']
        else:
            # 如果未提供enabled参数，则切换当前状态
            config_util.load_config()
            enabled = not config_util.config.get('source', {}).get('record', {}).get('enabled', True)

        # 加载并更新配置
        config_util.load_config()
        if 'source' not in config_util.config:
            config_util.config['source'] = {}
        if 'record' not in config_util.config['source']:
            config_util.config['source']['record'] = {}

        config_util.config['source']['record']['enabled'] = enabled
        config_util.save_config_sections(config_util.config, ('source',))
        config_util.load_config()
        _log_admin_action('microphone_toggle', 'source.record.enabled', {'enabled': enabled})

        return jsonify({
            'status': 'success',
            'enabled': enabled,
            'msg': f'麦克风已{"开启" if enabled else "关闭"}'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'msg': f'麦克风开关操作失败: {str(e)}'
        }), 500


#消息透传接口
@__app.route('/transparent-pass', methods=['post'])
def transparent_pass():
    try:
        data = request.form.get('data')
        if data is None:
            data = request.get_json(silent=True) or {}
        else:
            data = json.loads(data)

        if isinstance(data, dict):
            nested_data = data.get('data')
            if isinstance(nested_data, dict):
                data = nested_data
            elif isinstance(nested_data, str):
                nested_data = nested_data.strip()
                if nested_data:
                    try:
                        data = json.loads(nested_data)
                    except Exception:
                        pass

        if not isinstance(data, dict):
            data = {}

        username = data.get('user', 'User')
        response_text = data.get('text', None)
        audio_url = data.get('audio', None)
        if isinstance(audio_url, str):
            audio_url = audio_url.strip()
            if audio_url:
                parsed_audio = urlparse(audio_url)
                if not parsed_audio.scheme:
                    if audio_url.startswith('//'):
                        audio_url = 'http:' + audio_url
                    else:
                        base_url = ''
                        origin = (request.headers.get('Origin') or '').strip()
                        referer = (request.headers.get('Referer') or '').strip()
                        if origin:
                            parsed_origin = urlparse(origin)
                            if parsed_origin.scheme and parsed_origin.netloc:
                                base_url = f'{parsed_origin.scheme}://{parsed_origin.netloc}/'
                        if (not base_url) and referer:
                            parsed_referer = urlparse(referer)
                            if parsed_referer.scheme and parsed_referer.netloc:
                                base_url = f'{parsed_referer.scheme}://{parsed_referer.netloc}/'
                        if not base_url:
                            base_url = request.host_url
                        audio_url = urljoin(base_url, audio_url)
            else:
                audio_url = None

        queue_mode = _as_bool(data.get('queue', False))
        if not queue_mode:
            queue_mode = _as_bool(data.get('queue_playback', data.get('enqueue', False)))
        if not queue_mode:
            queue_mode = str(data.get('mode', '')).strip().lower() == 'queue'
        if not queue_mode:
            queue_mode = _as_bool(data.get('qutue', False))

        if response_text or audio_url:
            if queue_mode:
                interact = Interact('transparent_pass', 2, {
                    'user': username,
                    'text': response_text,
                    'audio': audio_url,
                    'isend': True,
                    'isfirst': True,
                    'no_reply': True,
                    'queue': True,
                    'queue_playback': True
                })
            else:
                util.printInfo(1, username, f'[\u0041\u0050\u0049\u4e2d\u65ad] \u65b0\u6d88\u606f\u5230\u8fbe\uff0c\u5b8c\u6574\u4e2d\u65ad\u7528\u6237 {username} \u4e4b\u524d\u7684\u6240\u6709\u5904\u7406')
                util.printInfo(1, username, f'[\u0041\u0050\u0049\u4e2d\u65ad] \u7528\u6237 {username} \u7684\u6587\u672c\u6d41\u548c\u97f3\u9891\u961f\u5217\u5df2\u6e05\u7a7a\uff0c\u51c6\u5907\u5904\u7406\u65b0\u6d88\u606f')
                interact = Interact('transparent_pass', 2, {
                    'user': username,
                    'text': response_text,
                    'audio': audio_url,
                    'isend': True,
                    'isfirst': True
                })

            util.printInfo(1, username, '\u900f\u4f20\u64ad\u653e\uff1a{},{}'.format(response_text, audio_url), time.time())
            success = fay_booter.feiFei.on_interact(interact)
            if success == 'success':
                return jsonify({'code': 200, 'message': '\u6210\u529f'})

        return jsonify({'code': 500, 'message': '\u672a\u77e5\u539f\u56e0\u51fa\u9519'})
    except Exception as e:
        return jsonify({'code': 500, 'message': f'\u51fa\u9519: {e}'}), 500
@__app.route('/api/clear-memory', methods=['POST'])
@auth_service.require_auth
@auth_service.require_role('admin')
def api_clear_memory():
    try:
        config_util.load_config()
        success_messages = []
        error_messages = []

        # 清除认知记忆（文件系统）
        try:
            memory_dir = os.path.join(os.getcwd(), "memory")

            if os.path.exists(memory_dir):
                # 清空memory目录下的所有文件
                for root, dirs, files in os.walk(memory_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                                util.log(1, f"已删除文件: {file_path}")
                        except Exception as e:
                            util.log(1, f"删除文件时出错: {file_path}, 错误: {str(e)}")

                # 创建标记文件，延迟到启动时删除chroma_db（避免文件锁定问题）
                with open(os.path.join(memory_dir, ".memory_cleared"), "w") as f:
                    f.write("Memory has been cleared. Do not save on exit.")

                # 清除内存中的认知记忆
                try:
                    from llm.nlp_cognitive_stream import set_memory_cleared_flag, clear_agent_memory as clear_cognitive
                    set_memory_cleared_flag(True)
                    clear_cognitive()
                    util.log(1, "已同时清除文件存储和内存中的认知记忆")
                except Exception as e:
                    util.log(1, f"清除内存中认知记忆时出错: {str(e)}")

                success_messages.append("认知记忆")
                util.log(1, "认知记忆已清除，ChromaDB数据库将在下次启动时清除")
            else:
                error_messages.append("记忆目录不存在")

        except Exception as e:
            error_messages.append(f"清除认知记忆时出错: {str(e)}")
            util.log(1, f"清除认知记忆时出错: {str(e)}")

        # 返回结果
        if success_messages:
            message = "已清除：" + "、".join(success_messages)
            if error_messages:
                message += "；部分失败：" + "、".join(error_messages)
            message += "，请重启应用使更改生效"
            _log_admin_action('memory_clear', 'memory', {'cleared': success_messages, 'errors': error_messages})
            return jsonify({'success': True, 'message': message}), 200
        else:
            message = "清除失败：" + "、".join(error_messages)
            return jsonify({'success': False, 'message': message}), 500

    except Exception as e:
        util.log(1, f"清除记忆时出错: {str(e)}")
        return jsonify({'success': False, 'message': f'清除记忆时出错: {str(e)}'}), 500

# 启动genagents_flask.py的API
@__app.route('/api/start-genagents', methods=['POST'])
@auth_service.require_auth
@auth_service.require_role('admin')
def api_start_genagents():
    try:
        config_util.load_config()

        # 只有在数字人启动后才能克隆人格
        if not fay_booter.is_running():
            return jsonify({'success': False, 'message': 'Fay未启动，无法启动决策分析'}), 400
        
        # 获取克隆要求
        data = request.get_json()
        if not data or 'instruction' not in data:
            return jsonify({'success': False, 'message': '缺少克隆要求参数'}), 400
        
        instruction = data['instruction']
        
        # 保存指令到临时文件，供genagents_flask.py读取
        instruction_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'genagents', 'instruction.json')
        with open(instruction_file, 'w', encoding='utf-8') as f:
            json.dump({'instruction': instruction}, f, ensure_ascii=False)
        
        # 导入genagents_flask模块
        import sys
        sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
        from genagents.genagents_flask import start_genagents_server, is_shutdown_requested
        from werkzeug.serving import make_server
        
        # 关闭之前的genagents服务器（如果存在）
        global genagents_server, genagents_thread, monitor_thread
        if genagents_server is not None:
            try:
                # 主动关闭之前的服务器
                util.log(1, "关闭之前的决策分析服务...")
                genagents_server.shutdown()
                # 等待线程结束
                if genagents_thread and genagents_thread.is_alive():
                    genagents_thread.join(timeout=2)
                if monitor_thread and monitor_thread.is_alive():
                    monitor_thread.join(timeout=2)
            except Exception as e:
                util.log(1, f"关闭之前的决策分析服务时出错: {str(e)}")
        
        # 清除之前的记忆，确保只保留最新的决策分析
        try:
            from llm.nlp_cognitive_stream import clear_agent_memory
            util.log(1, "已清除之前的决策分析记忆")
        except Exception as e:
            util.log(1, f"清除之前的决策分析记忆时出错: {str(e)}")
        
        # 启动决策分析服务（不启动单独进程，而是返回Flask应用实例）
        genagents_app = start_genagents_server(instruction_text=instruction)
        
        # 创建服务器
        genagents_server = make_server('0.0.0.0', 5001, genagents_app)
        
        # 在后台线程中启动Flask服务
        import threading
        def run_genagents_app():
            try:
                # 使用serve_forever而不是app.run
                genagents_server.serve_forever()
            except Exception as e:
                util.log(1, f"决策分析服务运行出错: {str(e)}")
            finally:
                util.log(1, f"决策分析服务已关闭")
        
        # 启动监控线程，检查是否需要关闭服务器
        def monitor_shutdown():
            try:
                while not is_shutdown_requested():
                    gsleep(1)
                util.log(1, f"检测到关闭请求，正在关闭决策分析服务...")
                genagents_server.shutdown()
            except Exception as e:
                util.log(1, f"监控决策分析服务时出错: {str(e)}")
        
        # 启动服务器线程
        genagents_thread = threading.Thread(target=run_genagents_app)
        genagents_thread.daemon = True
        genagents_thread.start()
        
        # 启动监控线程
        monitor_thread = threading.Thread(target=monitor_shutdown)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        util.log(1, f"已启动决策分析页面，指令: {instruction}")
        _log_admin_action('genagents_start', 'genagents', {'instruction_length': len(instruction)})

        # 返回决策分析页面的URL
        return jsonify({
            'success': True, 
            'message': '已启动决策分析页面',
            'url': 'http://127.0.0.1:5001/'
        }), 200
    except Exception as e:
        util.log(1, f"启动决策分析页面时出错: {str(e)}")
        return jsonify({'success': False, 'message': f'启动决策分析页面时出错: {str(e)}'}), 500

# 获取本地图片（用于在网页中显示本地图片）
@__app.route('/api/local-image')
def api_local_image():
    try:
        file_path = request.args.get('path', '')
        if not file_path:
            return jsonify({'error': '缺少文件路径参数'}), 400

        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({'error': f'文件不存在: {file_path}'}), 404

        # 检查是否为图片文件
        valid_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')
        if not file_path.lower().endswith(valid_extensions):
            return jsonify({'error': '不是有效的图片文件'}), 400

        # 返回图片文件
        return send_file(file_path)
    except Exception as e:
        return jsonify({'error': f'获取图片时出错: {str(e)}'}), 500

# 打开图片文件（使用系统默认程序）
@__app.route('/api/open-image', methods=['POST'])
def api_open_image():
    try:
        data = request.get_json()
        if not data or 'path' not in data:
            return jsonify({'success': False, 'message': '缺少文件路径参数'}), 400

        file_path = data['path']

        # 检查文件是否存在
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': f'文件不存在: {file_path}'}), 404

        # 检查是否为图片文件
        valid_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')
        if not file_path.lower().endswith(valid_extensions):
            return jsonify({'success': False, 'message': '不是有效的图片文件'}), 400

        # 使用系统默认程序打开图片
        import subprocess
        import platform

        system = platform.system()
        if system == 'Windows':
            os.startfile(file_path)
        elif system == 'Darwin':  # macOS
            subprocess.run(['open', file_path])
        else:  # Linux
            subprocess.run(['xdg-open', file_path])

        return jsonify({'success': True, 'message': '已打开图片'}), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'打开图片时出错: {str(e)}'}), 500

# 查询后台执行状态
@__app.route('/api/execution-status', methods=['GET'])
@auth_service.require_auth
def api_execution_status():
    try:
        from llm.execution_manager import get_execution_manager
        username = request.args.get('username', 'User')
        forbidden = _forbid_unless_self_or_admin(username)
        if forbidden:
            return forbidden
        mgr = get_execution_manager()
        state = mgr.get_state(username)
        if state is None:
            return jsonify({'status': 'idle', 'username': username})
        return jsonify({
            'status': state.status.value,
            'username': username,
            'original_request': state.original_request,
            'current_step': state.current_step,
            'steps_done': len(state.tool_results),
            'progress_messages': state.progress_messages[-10:],
            'elapsed': round((state.end_time or time.time()) - state.start_time, 1) if state.start_time else 0,
            'error': state.error,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 取消后台执行任务
@__app.route('/api/execution-cancel', methods=['POST'])
@auth_service.require_auth
def api_execution_cancel():
    try:
        from llm.execution_manager import get_execution_manager
        data = request.get_json() or {}
        username = data.get('username', 'User')
        forbidden = _forbid_unless_self_or_admin(username)
        if forbidden:
            return forbidden
        mgr = get_execution_manager()
        ok = mgr.cancel(username)
        return jsonify({'success': ok, 'username': username})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 向运行中的后台任务注入修改指令
@__app.route('/api/execution-modify', methods=['POST'])
@auth_service.require_auth
def api_execution_modify():
    try:
        from llm.execution_manager import get_execution_manager
        data = request.get_json() or {}
        username = data.get('username', 'User')
        forbidden = _forbid_unless_self_or_admin(username)
        if forbidden:
            return forbidden
        instruction = data.get('instruction', '')
        if not instruction:
            return jsonify({'success': False, 'message': '缺少 instruction 参数'}), 400
        mgr = get_execution_manager()
        ok = mgr.modify(username, instruction)
        return jsonify({'success': ok, 'username': username})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== 图片上传和管理接口 ====================

@__app.route('/api/upload-image', methods=['POST'])
def api_upload_image():
    """
    上传图片并保存到用户目录
    """
    from utils.image_storage import get_image_storage

    if 'image' not in request.files:
        return jsonify({'result': 'error', 'message': '未提供图片文件'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'result': 'error', 'message': '文件名为空'}), 400

    # 验证文件类型
    allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'}
    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if file_ext not in allowed_extensions:
        return jsonify({'result': 'error', 'message': f'不支持的文件格式，仅支持: {", ".join(allowed_extensions)}'}), 400

    # 生成唯一文件名
    unique_filename = f"{uuid.uuid4().hex}.{file_ext}"

    # 获取用户名（从表单或默认）
    username = request.form.get('username', 'User')

    # 读取文件内容
    file_content = file.read()

    # 检查文件大小（20MB限制）
    max_size = 20 * 1024 * 1024
    if len(file_content) > max_size:
        return jsonify({'result': 'error', 'message': '图片大小超过20MB'}), 400

    try:
        # 保存图片
        storage = get_image_storage()
        image_info = storage.save_image(
            file_content=file_content,
            filename=unique_filename,
            username=username,
            metadata={
                "original_filename": file.filename,
                "size": len(file_content),
                "mime_type": file.content_type
            }
        )

        return jsonify({
            'result': 'successful',
            'filename': image_info['filename'],
            'url': image_info['url'],
            'path': image_info['relative_path']
        })
    except Exception as e:
        util.log(1, f"图片上传失败: {e}")
        return jsonify({'result': 'error', 'message': f'保存图片失败: {e}'}), 500


@__app.route('/api/get-image/<username>/<date>/<filename>', methods=['GET'])
def api_get_image_by_user(username, date, filename):
    """
    获取用户的图片
    """
    from utils.image_storage import get_image_storage

    storage = get_image_storage()
    base_dir = os.path.abspath(storage.base_dir)
    image_dir = os.path.abspath(os.path.join(base_dir, username, date))
    if os.path.commonpath([base_dir, image_dir]) != base_dir:
        return jsonify({'error': '图片不存在'}), 404

    if not os.path.exists(image_dir):
        return jsonify({'error': '图片不存在'}), 404

    file_path = os.path.join(image_dir, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': '图片不存在'}), 404

    return send_from_directory(image_dir, filename)


@__app.route('/api/list-user-images', methods=['GET'])
def api_list_user_images():
    """
    列出用户的图片历史
    """
    from utils.image_storage import get_image_storage

    username = request.args.get('username', 'User')
    date = request.args.get('date')  # 可选，格式 YYYY-MM-DD
    limit = int(request.args.get('limit', 100))

    try:
        storage = get_image_storage()
        images = storage.list_user_images(username, date, limit)

        return jsonify({
            'result': 'successful',
            'images': images,
            'count': len(images)
        })
    except Exception as e:
        return jsonify({'result': 'error', 'message': str(e)}), 500


@__app.route('/api/cleanup-images', methods=['POST'])
def api_cleanup_images():
    """
    手动触发图片清理

    POST Body:
    {
        "days": 7,              # 可选，保留天数
        "username": "User",     # 可选，指定用户
        "dry_run": false        # 可选，预览模式
    }
    """
    from utils.image_storage import get_image_storage

    data = request.get_json() or {}

    days = data.get('days', 7)
    username = data.get('username')
    dry_run = data.get('dry_run', False)

    try:
        storage = get_image_storage()
        result = storage.cleanup_old_images(days=days, username=username, dry_run=dry_run)

        return jsonify({
            'result': 'successful',
            'mode': 'preview' if dry_run else 'executed',
            'deleted_dirs': result['deleted_dirs'],
            'deleted_files': result['deleted_files'],
            'freed_space_mb': result['freed_space_mb'],
            'errors': result['errors']
        })
    except Exception as e:
        util.log(1, f"图片清理失败: {e}")
        return jsonify({'result': 'error', 'message': str(e)}), 500


@__app.route('/api/image-storage-stats', methods=['GET'])
def api_image_storage_stats():
    """
    获取图片存储统计信息

    Query Params:
        username: 可选，指定用户
    """
    from utils.image_storage import get_image_storage

    username = request.args.get('username')

    try:
        storage = get_image_storage()
        stats = storage.get_storage_stats(username=username)

        return jsonify({
            'result': 'successful',
            'stats': stats
        })
    except Exception as e:
        return jsonify({'result': 'error', 'message': str(e)}), 500


def run():
    class NullLogHandler:
        def write(self, *args, **kwargs):
            pass
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    from werkzeug.serving import make_server
    server = make_server('0.0.0.0', 5000, __app, threaded=True)
    server.serve_forever()

def start():
    MyThread(target=run).start()
