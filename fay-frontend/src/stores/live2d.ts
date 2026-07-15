import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import {
  activateDigitalHuman as activateDigitalHumanApi,
  getActiveDigitalHuman,
  getDigitalHumans,
  updateDigitalHuman,
} from '../api/digitalHumans';
import { getLive2dUrl } from '../api/live';
import type { DigitalHuman, DigitalHumanPayload, DigitalHumanType } from '../types';

export const useLive2dStore = defineStore('live2d', () => {
  const iframeUrl = ref(getLive2dUrl());
  const lastCommand = ref('');
  const items = ref<DigitalHuman[]>([]);
  const activeId = ref('');
  const activeItem = ref<DigitalHuman | null>(null);
  const keyword = ref('');
  const typeFilter = ref<DigitalHumanType | ''>('');
  const activeHuman = computed(() => {
    if (activeItem.value?.id === activeId.value) {
      return activeItem.value;
    }
    return items.value.find((item) => item.id === activeId.value) || null;
  });
  const activeRenderUrl = computed(() => activeHuman.value?.render_url || '');

  function updateUrl(url: string) {
    iframeUrl.value = url.trim() || getLive2dUrl();
  }

  function rememberCommand(command: string) {
    lastCommand.value = command;
  }

  function upsertHuman(human: DigitalHuman) {
    const index = items.value.findIndex((item) => item.id === human.id);
    if (index === -1) {
      items.value.unshift(human);
    } else {
      items.value[index] = human;
    }
    if (activeId.value === human.id) {
      activeItem.value = human;
      iframeUrl.value = human.render_url || iframeUrl.value;
    }
  }

  async function loadDigitalHumans() {
    const data = await getDigitalHumans({ keyword: keyword.value, type: typeFilter.value });
    items.value = data.items || [];
    activeId.value = data.active_id || data.active?.id || '';
    activeItem.value = data.active || items.value.find((item) => item.id === activeId.value) || null;
    if (activeHuman.value?.render_url) {
      iframeUrl.value = activeHuman.value.render_url;
    }
    return items.value;
  }

  async function loadActiveDigitalHuman() {
    const data = await getActiveDigitalHuman();
    receiveDigitalHuman(data.digital_human, data.digital_human.id);
    return data.digital_human;
  }

  async function activateDigitalHuman(id: string) {
    const data = await activateDigitalHumanApi(id);
    activeId.value = data.digital_human.id;
    activeItem.value = data.digital_human;
    upsertHuman(data.digital_human);
    iframeUrl.value = data.digital_human.render_url || iframeUrl.value;
    return data.digital_human;
  }

  async function saveDigitalHuman(id: string, payload: DigitalHumanPayload) {
    const data = await updateDigitalHuman(id, payload);
    upsertHuman(data.digital_human);
    return data.digital_human;
  }

  function receiveDigitalHuman(human: DigitalHuman, nextActiveId?: string) {
    upsertHuman(human);
    if (nextActiveId !== undefined) {
      activeId.value = nextActiveId;
    } else if (!activeId.value) {
      activeId.value = human.id;
    }
    if (activeId.value === human.id) {
      activeItem.value = human;
    }
    if (activeHuman.value?.render_url) {
      iframeUrl.value = activeHuman.value.render_url;
    }
  }

  return {
    iframeUrl,
    lastCommand,
    items,
    activeId,
    keyword,
    typeFilter,
    activeHuman,
    activeRenderUrl,
    updateUrl,
    rememberCommand,
    loadDigitalHumans,
    loadActiveDigitalHuman,
    activateDigitalHuman,
    saveDigitalHuman,
    receiveDigitalHuman,
  };
});
