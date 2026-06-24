import { computed, ref } from 'vue';
import { defineStore } from 'pinia';
import { getBackgrounds, type BackgroundItem } from '../api/backgrounds';

const STORAGE_KEY = 'fay_background_state';
const DEFAULT_BACKGROUND_URL = '/frontend-static/images/digital-human-default.gif';
const DEFAULT_BACKGROUND: BackgroundItem = {
  id: 'default',
  name: '默认背景',
  url: DEFAULT_BACKGROUND_URL,
  builtin: true,
};

interface StoredBackgroundState {
  activeId?: string;
  manualUrl?: string;
}

function readStoredState(): StoredBackgroundState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) as StoredBackgroundState : {};
  } catch {
    return {};
  }
}

function persistState(state: StoredBackgroundState) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

export const useBackgroundStore = defineStore('background', () => {
  const stored = readStoredState();
  const activeId = ref(stored.activeId || 'server');
  const manualUrl = ref(stored.manualUrl || '');
  const backgrounds = ref<BackgroundItem[]>([DEFAULT_BACKGROUND]);
  const serverActiveId = ref('default');
  const loading = ref(false);
  const error = ref('');

  const resolvedActiveId = computed(() => (
    activeId.value === 'server' ? serverActiveId.value : activeId.value
  ));

  const activeBackground = computed(() => (
    backgrounds.value.find((item) => item.id === resolvedActiveId.value) || DEFAULT_BACKGROUND
  ));

  const activeBackgroundUrl = computed(() => {
    if (activeId.value === 'manual' && manualUrl.value) {
      return manualUrl.value;
    }
    return activeBackground.value.url;
  });

  const activeBackgroundName = computed(() => (
    activeId.value === 'manual' && manualUrl.value ? '自定义背景' : activeBackground.value.name
  ));

  function setManualBackground(url: string) {
    const nextUrl = url.trim();
    if (!nextUrl) {
      return;
    }
    manualUrl.value = nextUrl;
    activeId.value = 'manual';
    persistState({ activeId: activeId.value, manualUrl: manualUrl.value });
  }

  async function loadBackgrounds() {
    loading.value = true;
    error.value = '';
    try {
      const data = await getBackgrounds();
      backgrounds.value = normalizeBackgrounds(data.items || []);
      serverActiveId.value = data.active_id || data.active?.id || 'default';
    } catch (exc) {
      error.value = exc instanceof Error ? exc.message : '加载背景图失败';
    } finally {
      loading.value = false;
    }
  }

  function selectBackground(id: string) {
    if (!backgrounds.value.some((item) => item.id === id)) {
      return;
    }
    activeId.value = id;
    persistState({ activeId: activeId.value, manualUrl: manualUrl.value });
  }

  function useDefaultBackground() {
    activeId.value = 'default';
    persistState({ activeId: activeId.value, manualUrl: manualUrl.value });
  }

  return {
    activeId,
    manualUrl,
    backgrounds,
    loading,
    error,
    activeBackgroundUrl,
    activeBackgroundName,
    loadBackgrounds,
    selectBackground,
    setManualBackground,
    useDefaultBackground,
  };
});

function normalizeBackgrounds(items: BackgroundItem[]) {
  const withoutDefault = items.filter((item) => item.id !== DEFAULT_BACKGROUND.id);
  return [items.find((item) => item.id === DEFAULT_BACKGROUND.id) || DEFAULT_BACKGROUND, ...withoutDefault];
}
