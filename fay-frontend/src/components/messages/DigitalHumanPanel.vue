<script setup lang="ts">
import { useLive2dStore } from '../../stores/live2d';

const live2d = useLive2dStore();
</script>

<template>
  <aside class="digital-human-panel" aria-label="数字人">
    <iframe
      :src="live2d.iframeUrl"
      title="Live2D 数字人"
      allowtransparency="true"
      sandbox="allow-scripts allow-same-origin"
    />
  </aside>
</template>
