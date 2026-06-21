import { describe, expect, it, vi } from 'vitest';
import { computed, ref } from 'vue';
import { useVoiceInput } from './useVoiceInput';

class FakeMediaRecorder {
  static instance: FakeMediaRecorder | null = null;
  ondataavailable: ((event: { data: Blob }) => void) | null = null;
  onstop: (() => void) | null = null;
  state = 'inactive';

  constructor() {
    FakeMediaRecorder.instance = this;
  }

  start() {
    this.state = 'recording';
  }

  stop() {
    this.state = 'inactive';
    this.ondataavailable?.({ data: new Blob(['audio'], { type: 'audio/webm' }) });
    this.onstop?.();
  }
}

describe('useVoiceInput', () => {
  it('uploads stopped recording text and auto sends it', async () => {
    const submitMessage = vi.fn();
    const stopTrack = vi.fn();
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ success: true, text: '你好呀' }),
    });
    vi.stubGlobal('fetch', fetchMock);
    vi.stubGlobal('MediaRecorder', FakeMediaRecorder);
    vi.stubGlobal('navigator', {
      mediaDevices: {
        getUserMedia: vi.fn().mockResolvedValue({ getTracks: () => [{ stop: stopTrack }] }),
      },
    });

    const newMessage = ref('');
    const voiceInput = useVoiceInput({
      selectedUsername: computed(() => 'User'),
      selectedSessionId: computed(() => 9),
      newMessage,
      getLiveState: () => 1,
      submitMessage,
    });

    await voiceInput.startRecording();
    await voiceInput.stopRecording();
    await Promise.resolve();

    expect(fetchMock).toHaveBeenCalledWith('/api/asr/transcribe', expect.objectContaining({ method: 'POST' }));
    const formData = fetchMock.mock.calls[0][1].body as FormData;
    expect(formData.get('username')).toBe('User');
    expect(formData.get('session_id')).toBe('9');
    expect(newMessage.value).toBe('你好呀');
    expect(submitMessage).toHaveBeenCalledTimes(1);
    expect(stopTrack).toHaveBeenCalledTimes(1);
  });
});
