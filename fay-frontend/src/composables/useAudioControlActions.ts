import type { ComputedRef } from 'vue';
import { ElMessage } from 'element-plus';
import { BRAND_SERVICE_NAME } from '../config/brand';
import type { AudioConfig, AudioFlag } from '../utils/audioControls';

interface AudioControlStore {
  audioConfig: AudioConfig;
  toggleAudioConfig(key: AudioFlag): Promise<void>;
  setContinuousVoice(enabled: boolean, username: string, sessionId: number | null): Promise<void>;
  startLive(): Promise<void>;
}

interface VoiceContext {
  selectedUsername: ComputedRef<string>;
  selectedSessionId: ComputedRef<number | null>;
}

export function useAudioControlActions(appStore: AudioControlStore, context: VoiceContext) {
  async function toggleAudio(key: AudioFlag) {
    try {
      await appStore.toggleAudioConfig(key);
    } catch (error) {
      ElMessage.error(error instanceof Error ? error.message : '保存音频设置失败');
    }
  }

  async function toggleMic() {
    const enabled = !appStore.audioConfig.mic;
    const sessionId = context.selectedSessionId.value;
    if (enabled && sessionId === null) {
      ElMessage.warning('请先选择会话');
      return;
    }
    try {
      await appStore.setContinuousVoice(enabled, context.selectedUsername.value, sessionId);
    } catch (error) {
      ElMessage.error(error instanceof Error ? error.message : '切换连续对话失败');
    }
  }

  async function stopContinuousVoiceForContextChange() {
    if (!appStore.audioConfig.mic || appStore.audioConfig.micMode !== 'continuous') {
      return;
    }
    try {
      await appStore.setContinuousVoice(
        false,
        context.selectedUsername.value,
        context.selectedSessionId.value,
      );
    } catch (error) {
      ElMessage.error(error instanceof Error ? error.message : '切换会话时关闭连续对话失败');
    }
  }

  async function startLiveFromComposer() {
    try {
      await appStore.startLive();
    } catch (error) {
      ElMessage.error(error instanceof Error ? error.message : `启动 ${BRAND_SERVICE_NAME} 失败`);
    }
  }

  return {
    toggleMic,
    stopContinuousVoiceForContextChange,
    toggleSpeaker: () => toggleAudio('speaker'),
    startLiveFromComposer,
  };
}
