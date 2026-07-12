import os
import shutil
import subprocess


ASR_SAMPLE_RATE = 16000
FFMPEG_TIMEOUT_SECONDS = 60


class AudioConversionError(RuntimeError):
    pass


def normalize_audio_for_asr(source_path):
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        raise AudioConversionError("FFmpeg 未安装或不在 PATH 中")

    output_path = f"{os.path.splitext(source_path)[0]}.normalized.wav"
    command = [
        ffmpeg_path,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        source_path,
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(ASR_SAMPLE_RATE),
        "-c:a",
        "pcm_s16le",
        output_path,
    ]
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=FFMPEG_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        _remove_output(output_path)
        raise AudioConversionError("FFmpeg 音频转换超时") from exc

    if result.returncode != 0 or not _has_audio_output(output_path):
        _remove_output(output_path)
        detail = (result.stderr or "未知错误").strip()
        raise AudioConversionError(f"FFmpeg 音频转换失败: {detail}")
    return output_path


def _has_audio_output(path):
    return os.path.exists(path) and os.path.getsize(path) > 0


def _remove_output(path):
    if os.path.exists(path):
        os.remove(path)
