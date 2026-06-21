import { computed, ref } from 'vue';
import { defineStore } from 'pinia';

const STORAGE_KEY = 'fay_background_state';
const DEFAULT_BACKGROUND_URL = '/frontend-static/images/digital-human-default.gif';

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
  const activeId = ref(stored.activeId || 'default');
  const manualUrl = ref(stored.manualUrl || '');

  const activeBackgroundUrl = computed(() => {
    if (activeId.value === 'manual' && manualUrl.value) {
      return manualUrl.value;
    }
    return DEFAULT_BACKGROUND_URL;
  });

  const activeBackgroundName = computed(() => (
    activeId.value === 'manual' && manualUrl.value ? '自定义背景' : '默认背景'
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

  function useDefaultBackground() {
    activeId.value = 'default';
    persistState({ activeId: activeId.value, manualUrl: manualUrl.value });
  }

  return {
    activeId,
    manualUrl,
    activeBackgroundUrl,
    activeBackgroundName,
    setManualBackground,
    useDefaultBackground,
  };
});

