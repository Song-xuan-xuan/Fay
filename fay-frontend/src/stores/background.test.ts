import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useBackgroundStore } from './background';

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
});
