import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useAppStore } from './app';
import { useAuthStore } from './auth';
import { getMemberList } from '../api/message';

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
});
