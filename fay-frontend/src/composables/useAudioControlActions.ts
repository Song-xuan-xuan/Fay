import { ElMessage } from 'element-plus';
import type { AudioConfig } from '../utils/audioControls';

interface AudioControlStore {
  toggleAudioConfig(key: keyof AudioConfig): Promise<void>;
  startLive(): Promise<void>;
}

export function useAudioControlActions(appStore: AudioControlStore) {
  async function toggleAudio(key: keyof AudioConfig) {
    try {
      await appStore.toggleAudioConfig(key);
    } catch (error) {
      ElMessage.error(error instanceof Error ? error.message : '保存音频设置失败');
    }
  }

  async function startLiveFromComposer() {
    try {
      await appStore.startLive();
    } catch (error) {
      ElMessage.error(error instanceof Error ? error.message : '启动 Fay 服务失败');
    }
  }

  return {
    toggleMic: () => toggleAudio('mic'),
    toggleSpeaker: () => toggleAudio('speaker'),
    startLiveFromComposer,
  };
}
