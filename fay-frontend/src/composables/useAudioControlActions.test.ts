import { computed } from 'vue';
import { describe, expect, it, vi } from 'vitest';
import { useAudioControlActions } from './useAudioControlActions';

describe('useAudioControlActions', () => {
  it('opens and closes continuous conversation for the selected session', async () => {
    const store = {
      audioConfig: { mic: false, speaker: true, micMode: 'wake' as const },
      toggleAudioConfig: vi.fn(),
      setContinuousVoice: vi.fn().mockResolvedValue(undefined),
      startLive: vi.fn(),
    };
    const actions = useAudioControlActions(store, {
      selectedUsername: computed(() => 'alice'),
      selectedSessionId: computed(() => 9),
    });

    await actions.toggleMic();
    expect(store.setContinuousVoice).toHaveBeenLastCalledWith(true, 'alice', 9);

    store.audioConfig.mic = true;
    await actions.toggleMic();
    expect(store.setContinuousVoice).toHaveBeenLastCalledWith(false, 'alice', 9);
  });

  it('closes continuous conversation when the selected context changes', async () => {
    const store = {
      audioConfig: { mic: true, speaker: true, micMode: 'continuous' as const },
      toggleAudioConfig: vi.fn(),
      setContinuousVoice: vi.fn().mockResolvedValue(undefined),
      startLive: vi.fn(),
    };
    const actions = useAudioControlActions(store, {
      selectedUsername: computed(() => 'bob'),
      selectedSessionId: computed(() => 12),
    });

    await actions.stopContinuousVoiceForContextChange();

    expect(store.setContinuousVoice).toHaveBeenCalledWith(false, 'bob', 12);
  });

  it('does nothing on context changes when continuous conversation is off', async () => {
    const store = {
      audioConfig: { mic: false, speaker: true, micMode: 'continuous' as const },
      toggleAudioConfig: vi.fn(),
      setContinuousVoice: vi.fn().mockResolvedValue(undefined),
      startLive: vi.fn(),
    };
    const actions = useAudioControlActions(store, {
      selectedUsername: computed(() => 'bob'),
      selectedSessionId: computed(() => 12),
    });

    await actions.stopContinuousVoiceForContextChange();

    expect(store.setContinuousVoice).not.toHaveBeenCalled();
  });
});
