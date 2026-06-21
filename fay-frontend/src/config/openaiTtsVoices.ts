import type { VoiceOption } from '../types';

export interface NormalizedVoiceOption {
  value: string;
  label: string;
}

export const OPENAI_CHINESE_TTS_VOICES: NormalizedVoiceOption[] = [
  { value: 'zh-CN-XiaoxiaoNeural', label: '晓晓（女声）' },
  { value: 'zh-CN-XiaoyiNeural', label: '晓伊（女声）' },
  { value: 'zh-CN-YunjianNeural', label: '云健（男声）' },
  { value: 'zh-CN-YunxiNeural', label: '云希（男声）' },
  { value: 'zh-CN-YunxiaNeural', label: '云夏（男声）' },
  { value: 'zh-CN-YunyangNeural', label: '云阳（男声）' },
  { value: 'zh-CN-liaoning-XiaobeiNeural', label: '小贝（辽宁女声）' },
  { value: 'zh-CN-shaanxi-XiaoniNeural', label: '晓妮（陕西女声）' },
  { value: 'zh-HK-HiuGaaiNeural', label: '晓佳（香港女声）' },
  { value: 'zh-HK-HiuMaanNeural', label: '晓曼（香港女声）' },
  { value: 'zh-HK-WanLungNeural', label: '云龙（香港男声）' },
  { value: 'zh-TW-HsiaoChenNeural', label: '晓臻（台湾女声）' },
  { value: 'zh-TW-HsiaoYuNeural', label: '晓雨（台湾女声）' },
  { value: 'zh-TW-YunJheNeural', label: '云哲（台湾男声）' },
];

function normalizeVoice(voice: VoiceOption): NormalizedVoiceOption {
  const value = voice.value || voice.id || '';
  return {
    value,
    label: voice.label || voice.name || value,
  };
}

function isChineseNeuralVoice(value: string) {
  return /^zh-[A-Za-z-]+Neural$/.test(value);
}

function isChineseNeuralVoiceList(voices: NormalizedVoiceOption[]) {
  return voices.length > 0 && voices.every((voice) => isChineseNeuralVoice(voice.value));
}

export function normalizeVoiceOptions(voices: VoiceOption[] = []): NormalizedVoiceOption[] {
  const normalized = voices.map(normalizeVoice).filter((voice) => voice.value);
  if (isChineseNeuralVoiceList(normalized)) {
    return OPENAI_CHINESE_TTS_VOICES.map((voice) => ({ ...voice }));
  }
  return normalized;
}
