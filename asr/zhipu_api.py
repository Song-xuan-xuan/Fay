import os
import mimetypes

import requests

from core import wsa_server
from utils import config_util as cfg
from utils import util


DEFAULT_ZHIPU_ASR_URL = "https://open.bigmodel.cn/api/paas/v4/audio/transcriptions"
DEFAULT_ZHIPU_ASR_MODEL = "glm-asr-2512"
DEFAULT_ZHIPU_ASR_TIMEOUT = 30.0


def _get_timeout():
    raw_value = getattr(cfg, "asr_api_timeout", None)
    if raw_value is None or str(raw_value).strip() == "":
        return DEFAULT_ZHIPU_ASR_TIMEOUT
    try:
        timeout = float(raw_value)
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        return timeout
    except (TypeError, ValueError):
        util.log(2, f"[Zhipu ASR] asr_api_timeout配置无效，使用默认值: {DEFAULT_ZHIPU_ASR_TIMEOUT}")
        return DEFAULT_ZHIPU_ASR_TIMEOUT


def _parse_text(response):
    try:
        data = response.json()
    except ValueError:
        return ""
    if isinstance(data, dict):
        text = data.get("text") or data.get("result")
        return str(text).strip() if text else ""
    return ""


def _guess_audio_mime(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or "application/octet-stream"


def transcribe_file(file_path):
    url = getattr(cfg, "asr_api_url", None) or DEFAULT_ZHIPU_ASR_URL
    model = getattr(cfg, "asr_api_model", None) or DEFAULT_ZHIPU_ASR_MODEL
    api_key = getattr(cfg, "asr_api_key", None)
    if not api_key:
        util.log(2, "[Zhipu ASR] 未配置asr_api_key")
        return ""

    with open(file_path, "rb") as audio_file:
        files = {"file": (os.path.basename(file_path), audio_file, _guess_audio_mime(file_path))}
        data = {"model": model, "stream": "false"}
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.post(url, headers=headers, data=data, files=files, timeout=_get_timeout())

    if response.status_code != 200:
        util.log(1, f"[Zhipu ASR] 识别失败，状态码: {response.status_code}，响应: {response.text}")
        return ""
    return _parse_text(response)


class ZhipuASR:
    def __init__(self, username):
        self.username = username
        self.started = True
        self.done = False
        self.finalResults = ""

    def start(self):
        self.started = True

    def send(self, buf):
        pass

    def end(self):
        pass

    def send_url(self, wav_path):
        self.done = False
        self.finalResults = ""
        try:
            self.finalResults = self.__transcribe(wav_path)
            self.__notify_result(self.finalResults)
        except Exception as e:
            util.log(1, f"[Zhipu ASR] 请求失败: {e}")
        finally:
            self.done = True

    def __transcribe(self, wav_path):
        return transcribe_file(wav_path)

    def __notify_result(self, text):
        if not text:
            return
        web_instance = wsa_server.get_web_instance()
        human_instance = wsa_server.get_instance()
        if web_instance is not None and web_instance.is_connected(self.username):
            web_instance.add_cmd({"panelMsg": text, "Username": self.username})
        if human_instance is not None and human_instance.is_connected(self.username):
            content = {'Topic': 'human', 'Data': {'Key': 'log', 'Value': text}, 'Username': self.username}
            human_instance.add_cmd(content)
