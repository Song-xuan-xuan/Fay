<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useLive2dStore } from '../../stores/live2d';

const live2d = useLive2dStore();
const activeHuman = computed(() => live2d.activeHuman);

onMounted(() => {
  if (!activeHuman.value) {
    live2d.loadActiveDigitalHuman().catch(() => undefined);
  }
});
</script>

<template>
  <aside class="digital-human-panel" aria-label="数字人">
    <iframe
      v-if="activeHuman && activeHuman.type !== 'image' && activeHuman.render_url"
      :key="activeHuman.id"
      :src="activeHuman.render_url"
      :title="`${activeHuman.name} 数字人`"
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
