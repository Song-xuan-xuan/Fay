import type { FayConfig } from '../types';

export interface AudioConfig {
  mic: boolean;
  speaker: boolean;
}

export function toggleAudioFlag(config: AudioConfig, key: keyof AudioConfig): AudioConfig {
  return {
    ...config,
    [key]: !config[key],
  };
}

export function buildAudioConfigPatch(patch: Partial<AudioConfig>): FayConfig {
  const config: FayConfig = {};
  if (patch.mic !== undefined) {
    config.source = { record: { enabled: patch.mic } };
  }
  if (patch.speaker !== undefined) {
    config.interact = { playSound: patch.speaker };
  }
  return config;
}
