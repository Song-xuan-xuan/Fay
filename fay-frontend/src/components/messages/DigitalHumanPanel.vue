<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useAppStore } from '../../stores/app';
import { useAuthStore } from '../../stores/auth';
import { useLive2dStore } from '../../stores/live2d';
import {
  buildDigitalHumanRenderUrl,
  type DigitalHumanPanelContext,
} from '../../utils/digitalHumanRenderUrl';

const props = withDefaults(defineProps<{
  viewContext?: DigitalHumanPanelContext;
}>(), {
  viewContext: 'default',
});

const appStore = useAppStore();
const authStore = useAuthStore();
const live2d = useLive2dStore();
const activeHuman = computed(() => live2d.activeHuman);
const activeRenderUrl = computed(() => {
  if (!activeHuman.value?.render_url) {
    return '';
  }
  const username = appStore.selectedUser?.[1] || authStore.user?.username || 'User';
  return buildDigitalHumanRenderUrl(activeHuman.value, {
    token: authStore.token,
    username,
    panel: props.viewContext,
  });
});

onMounted(() => {
  if (!activeHuman.value) {
    live2d.loadActiveDigitalHuman().catch(() => undefined);
  }
});
</script>

<template>
  <aside class="digital-human-panel" aria-label="数字人">
    <iframe
      v-if="activeHuman && activeHuman.type !== 'image' && activeRenderUrl"
      :key="activeHuman.id"
      :src="activeRenderUrl"
      :title="`${activeHuman.name} 数字人`"
      allow="autoplay"
      allowtransparency="true"
      sandbox="allow-scripts allow-same-origin"
    />
    <img
      v-else-if="activeHuman && activeHuman.cover_url"
      class="digital-human-static"
      :src="activeHuman.cover_url"
      :alt="activeHuman.name"
    />
    <div v-else class="digital-human-placeholder" role="status">
      <strong>未设置数字人</strong>
      <span>请在数字人库中选择当前数字人。</span>
    </div>
  </aside>
</template>
