import time
import requests
from pydub import AudioSegment
from utils import util, config_util


class Speech:
    def connect(self):
        util.log(1, "OpenAI-compatible TTS 服务已准备")

    def close(self):
        pass

    def convert_mp3_to_wav(self, mp3_filepath):
        audio = AudioSegment.from_mp3(mp3_filepath)
        audio = audio.set_frame_rate(44100)
        wav_filepath = mp3_filepath.rsplit(".", 1)[0] + ".wav"
        audio.export(wav_filepath, format="wav")
        return wav_filepath

    def to_sample(self, text, style):
        url = "http://127.0.0.1:8080/v1/audio/speech"

        # 从配置文件读取音色，如果未配置则使用默认值
        voice = config_util.config.get("attribute", {}).get("voice")
        if not voice or str(voice).strip() == "":
            voice = "zh-CN-XiaoxiaoNeural"

        util.log(1, f"[OpenAI TTS] 使用音色: {voice}")

        payload = {
            "model": "tts-1",
            "voice": voice,
            "input": text,
            "response_format": "mp3"
        }

        util.log(1, f"[OpenAI TTS] 请求参数: {payload}")

        try:
            response = requests.post(url, json=payload, timeout=120)
            file_url = "./samples/sample-" + str(int(time.time() * 1000)) + ".mp3"

            if response.status_code == 200:
                with open(file_url, "wb") as f:
                    f.write(response.content)

                return self.convert_mp3_to_wav(file_url)

            util.log(1, "[x] OpenAI TTS 转换失败")
            util.log(1, "[x] 状态码: " + str(response.status_code))
            util.log(1, "[x] 原因: " + response.text)
            return None

        except Exception as e:
            util.log(1, "[x] OpenAI TTS 请求失败")
            util.log(1, "[x] 原因: " + str(e))
            return None