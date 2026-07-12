import type { FayConfig } from '../types';

export type VoiceInputMode = 'wake' | 'continuous';
export type AudioFlag = 'mic' | 'speaker';

export interface AudioConfig {
  mic: boolean;
  speaker: boolean;
  micMode: VoiceInputMode;
}

export function toggleAudioFlag(config: AudioConfig, key: AudioFlag): AudioConfig {
  return {
    ...config,
    [key]: !config[key],
  };
}

export function buildAudioConfigPatch(patch: Partial<AudioConfig>): FayConfig {
  const config: FayConfig = {};
  if (patch.mic !== undefined) {
    const record: Record<string, boolean | VoiceInputMode> = { enabled: patch.mic };
    if (patch.micMode !== undefined) {
      record.mode = patch.micMode;
    }
    config.source = { record };
  }
  if (patch.speaker !== undefined) {
    config.interact = { playSound: patch.speaker };
  }
  return config;
}
