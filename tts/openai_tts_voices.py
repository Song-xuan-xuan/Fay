OPENAI_TTS_VOICE_LIST = [
    {"id": "zh-CN-XiaoxiaoNeural", "name": "晓晓（女声）"},
    {"id": "zh-CN-XiaoyiNeural", "name": "晓伊（女声）"},
    {"id": "zh-CN-YunjianNeural", "name": "云健（男声）"},
    {"id": "zh-CN-YunxiNeural", "name": "云希（男声）"},
    {"id": "zh-CN-YunxiaNeural", "name": "云夏（男声）"},
    {"id": "zh-CN-YunyangNeural", "name": "云阳（男声）"},
    {"id": "zh-CN-liaoning-XiaobeiNeural", "name": "小贝（辽宁女声）"},
    {"id": "zh-CN-shaanxi-XiaoniNeural", "name": "晓妮（陕西女声）"},
    {"id": "zh-HK-HiuGaaiNeural", "name": "晓佳（香港女声）"},
    {"id": "zh-HK-HiuMaanNeural", "name": "晓曼（香港女声）"},
    {"id": "zh-HK-WanLungNeural", "name": "云龙（香港男声）"},
    {"id": "zh-TW-HsiaoChenNeural", "name": "晓臻（台湾女声）"},
    {"id": "zh-TW-HsiaoYuNeural", "name": "晓雨（台湾女声）"},
    {"id": "zh-TW-YunJheNeural", "name": "云哲（台湾男声）"},
]


def get_openai_tts_voice_list():
    return [voice.copy() for voice in OPENAI_TTS_VOICE_LIST]
