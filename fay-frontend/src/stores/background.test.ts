import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useBackgroundStore } from './background';
import { getBackgrounds } from '../api/backgrounds';

vi.mock('../api/backgrounds', () => ({
  getBackgrounds: vi.fn(),
}));

const storage = new Map<string, string>();

function installLocalStorage() {
  storage.clear();
  vi.stubGlobal('localStorage', {
    getItem: vi.fn((key: string) => storage.get(key) || null),
    setItem: vi.fn((key: string, value: string) => storage.set(key, value)),
    removeItem: vi.fn((key: string) => storage.delete(key)),
  });
}

describe('background store', () => {
  beforeEach(() => {
    installLocalStorage();
    vi.mocked(getBackgrounds).mockReset();
    setActivePinia(createPinia());
  });

  it('uses a built-in scenic background when no custom background is selected', () => {
    const store = useBackgroundStore();

    expect(store.activeBackgroundUrl).toContain('/frontend-static/');
    expect(store.activeBackgroundName).toBe('默认背景');
  });

  it('selects and persists a manually entered background URL', () => {
    const store = useBackgroundStore();

    store.setManualBackground('https://example.com/bg.jpg');

    expect(store.activeBackgroundUrl).toBe('https://example.com/bg.jpg');
    expect(store.activeBackgroundName).toBe('自定义背景');
    expect(localStorage.setItem).toHaveBeenCalledWith(
      'fay_background_state',
      expect.stringContaining('https://example.com/bg.jpg'),
    );
  });

  it('restores the selected background from local storage', () => {
    storage.set('fay_background_state', JSON.stringify({
      activeId: 'manual',
      manualUrl: 'https://example.com/restored.jpg',
    }));
    setActivePinia(createPinia());

    const store = useBackgroundStore();

    expect(store.activeBackgroundUrl).toBe('https://example.com/restored.jpg');
  });

  it('loads uploaded backgrounds and uses the server active background by default', async () => {
    vi.mocked(getBackgrounds).mockResolvedValue({
      success: true,
      active_id: 'bg_1',
      active: { id: 'bg_1', name: '大厅背景', url: '/backgrounds/lobby.png' },
      items: [
        { id: 'default', name: '默认背景', url: '/frontend-static/images/digital-human-default.gif', builtin: true },
        { id: 'bg_1', name: '大厅背景', url: '/backgrounds/lobby.png' },
      ],
    });
    const store = useBackgroundStore();

    await store.loadBackgrounds();

    expect(store.backgrounds).toHaveLength(2);
    expect(store.activeBackgroundUrl).toBe('/backgrounds/lobby.png');
    expect(store.activeBackgroundName).toBe('大厅背景');
  });

  it('selects an uploaded background locally without losing the manual URL', async () => {
    vi.mocked(getBackgrounds).mockResolvedValue({
      success: true,
      active_id: 'default',
      active: { id: 'default', name: '默认背景', url: '/frontend-static/images/digital-human-default.gif', builtin: true },
      items: [
        { id: 'default', name: '默认背景', url: '/frontend-static/images/digital-human-default.gif', builtin: true },
        { id: 'bg_1', name: '大厅背景', url: '/backgrounds/lobby.png' },
      ],
    });
    const store = useBackgroundStore();
    store.setManualBackground('https://example.com/manual.jpg');
    await store.loadBackgrounds();

    store.selectBackground('bg_1');

    expect(store.activeBackgroundUrl).toBe('/backgrounds/lobby.png');
    expect(store.manualUrl).toBe('https://example.com/manual.jpg');
    expect(localStorage.setItem).toHaveBeenLastCalledWith(
      'fay_background_state',
      expect.stringContaining('bg_1'),
    );
  });
});
