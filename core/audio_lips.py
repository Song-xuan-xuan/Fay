import math
import struct
import wave


FRAME_MS = 50
QUIET_THRESHOLD = 0.08
LOW_THRESHOLD = 0.32
MID_THRESHOLD = 0.62


def build_silent_lips(audio_length_seconds):
    """Build a minimal viseme timeline so Live2D clients accept audio without OVR lips."""
    try:
        duration_ms = int(float(audio_length_seconds) * 1000)
    except (TypeError, ValueError):
        return []
    if duration_ms <= 0:
        return []
    return [{"Lip": "sil", "Time": duration_ms}]


def build_energy_lips(audio_path, fallback_duration_seconds=None, frame_ms=FRAME_MS):
    try:
        samples = _read_pcm_frames(audio_path, frame_ms)
    except Exception:
        return build_silent_lips(fallback_duration_seconds)
    if not samples:
        return build_silent_lips(fallback_duration_seconds)
    max_rms = max(rms for rms, _ in samples)
    if max_rms <= 0:
        return build_silent_lips(_total_seconds(samples, fallback_duration_seconds))
    lips = []
    for rms, duration_ms in samples:
        lips.append({"Lip": _rms_to_viseme(rms / max_rms), "Time": duration_ms})
    return _merge_lips(lips)


def _read_pcm_frames(audio_path, frame_ms):
    with wave.open(audio_path, "rb") as wav_file:
        sample_width = wav_file.getsampwidth()
        channels = wav_file.getnchannels()
        sample_rate = wav_file.getframerate()
        frame_size = max(1, int(sample_rate * frame_ms / 1000))
        result = []
        while True:
            data = wav_file.readframes(frame_size)
            if not data:
                break
            duration_ms = round(len(data) / sample_width / channels / sample_rate * 1000)
            if duration_ms > 0:
                result.append((_pcm_rms(data, sample_width), duration_ms))
        return result


def _pcm_rms(data, sample_width):
    if sample_width == 1:
        values = (sample - 128 for sample in data)
    elif sample_width == 2:
        values = (item[0] for item in struct.iter_unpack("<h", data))
    elif sample_width == 4:
        values = (item[0] for item in struct.iter_unpack("<i", data))
    else:
        raise ValueError(f"unsupported wav sample width: {sample_width}")
    total = 0
    count = 0
    for value in values:
        total += value * value
        count += 1
    return math.sqrt(total / count) if count else 0


def _rms_to_viseme(level):
    if level < QUIET_THRESHOLD:
        return "sil"
    if level < LOW_THRESHOLD:
        return "ih"
    if level < MID_THRESHOLD:
        return "E"
    return "aa"


def _merge_lips(lips):
    merged = []
    for item in lips:
        if merged and merged[-1]["Lip"] == item["Lip"]:
            merged[-1]["Time"] += item["Time"]
        else:
            merged.append(dict(item))
    return merged


def _total_seconds(samples, fallback_duration_seconds):
    duration_ms = sum(duration_ms for _, duration_ms in samples)
    if duration_ms > 0:
        return duration_ms / 1000
    return fallback_duration_seconds
