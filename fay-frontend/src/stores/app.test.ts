import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useAppStore } from './app';
import { useAuthStore } from './auth';
import { getMemberList } from '../api/message';
import { getData, getRunStatus } from '../api/setting';

vi.mock('../api/message', () => ({
  getAudioConfig: vi.fn(),
  getChatSessions: vi.fn(),
  getMemberList: vi.fn(),
  getSystemStatus: vi.fn(),
}));

vi.mock('../api/setting', () => ({
  getData: vi.fn(),
  getRunStatus: vi.fn(),
  startLive: vi.fn(),
  stopLive: vi.fn(),
  submitConfig: vi.fn(),
}));

describe('useAppStore user selection state', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    const storage = new Map<string, string>();
    vi.stubGlobal('localStorage', {
      getItem: vi.fn((key: string) => storage.get(key) || null),
      setItem: vi.fn((key: string, value: string) => storage.set(key, value)),
      removeItem: vi.fn((key: string) => storage.delete(key)),
    });
    vi.mocked(getMemberList).mockReset();
    vi.mocked(getData).mockReset();
    vi.mocked(getRunStatus).mockReset();
  });

  it('keeps the selected user reference stable for repeated own-user loads', async () => {
    const authStore = useAuthStore();
    authStore.restoreSession({
      token: 'token',
      uid: 7,
      username: 'songxuan',
      role: 'user',
      avatar_path: '/avatar.png',
      must_change_password: false,
    });
    vi.mocked(getMemberList).mockResolvedValue([]);
    const appStore = useAppStore();

    await appStore.loadUsers();
    const selected = appStore.selectedUser;
    await appStore.loadUsers();

    expect(appStore.selectedUser).toBe(selected);
  });

  it('normalizes old OpenAI Chinese voice payloads to the full verified Chinese list', async () => {
    vi.mocked(getRunStatus).mockResolvedValue({ status: false });
    vi.mocked(getData).mockResolvedValue({
      config: {},
      voice_list: [
        { id: 'zh-CN-XiaoxiaoNeural', name: '晓晓（女声）' },
        { id: 'zh-CN-YunxiNeural', name: '云溪（男声）' },
        { id: 'zh-CN-YunyangNeural', name: '云阳（男声）' },
        { id: 'zh-CN-XiaoyiNeural', name: '晓伊（女声）' },
        { id: 'zh-CN-YunjianNeural', name: '云健（男声）' },
        { id: 'zh-CN-XiaoxuanNeural', name: '晓萱（女声）' },
        { id: 'zh-CN-YunxiaNeural', name: '云夏（女声）' },
      ],
    });
    const appStore = useAppStore();

    await appStore.loadBootstrapData();

    const voiceIds = appStore.voiceList.map((voice) => voice.value);
    expect(appStore.voiceList).toHaveLength(14);
    expect(voiceIds).toContain('zh-CN-liaoning-XiaobeiNeural');
    expect(voiceIds).toContain('zh-HK-WanLungNeural');
    expect(voiceIds).toContain('zh-TW-YunJheNeural');
    expect(voiceIds).not.toContain('zh-CN-XiaoxuanNeural');
    expect(appStore.voiceList.every((voice) => /（.+声）/.test(voice.label))).toBe(true);
  });

  it('normalizes websocket OpenAI Chinese voice payloads before updating editor options', () => {
    const appStore = useAppStore();

    appStore.receiveWebsocketPayload({
      voiceList: [
        { id: 'zh-CN-XiaoxiaoNeural', name: '晓晓（女声）' },
        { id: 'zh-CN-XiaoxuanNeural', name: '晓萱（女声）' },
      ],
    });

    const voiceIds = appStore.voiceList.map((voice) => voice.value);
    expect(appStore.voiceList).toHaveLength(14);
    expect(voiceIds).toContain('zh-CN-shaanxi-XiaoniNeural');
    expect(voiceIds).not.toContain('zh-CN-XiaoxuanNeural');
  });
});
