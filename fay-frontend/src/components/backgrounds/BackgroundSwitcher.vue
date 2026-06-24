<script setup lang="ts">
import { computed, onMounted, ref, type CSSProperties } from 'vue';
import { Image as ImageIcon, RefreshCw } from '@lucide/vue';
import { useBackgroundStore } from '../../stores/background';
import type { BackgroundItem } from '../../api/backgrounds';

const backgroundStore = useBackgroundStore();
const manualBackgroundUrl = ref('');

const selectableBackgrounds = computed(() => backgroundStore.backgrounds);

function previewStyle(background: BackgroundItem): CSSProperties {
  return {
    backgroundImage: `url("${background.url.replace(/"/g, '\\"')}")`,
  };
}

function setManualBackground() {
  backgroundStore.setManualBackground(manualBackgroundUrl.value);
  manualBackgroundUrl.value = '';
}

function selectBackground(id: string) {
  backgroundStore.selectBackground(id);
}

onMounted(() => {
  backgroundStore.loadBackgrounds().catch(() => undefined);
});
</script>

<template>
  <el-popover trigger="click" placement="bottom-end" width="340" popper-class="background-switcher-popper">
    <div class="background-switcher">
      <div class="background-switcher-head">
        <strong>背景图</strong>
        <span>{{ backgroundStore.activeBackgroundName }}</span>
      </div>

      <div class="background-options" v-loading="backgroundStore.loading">
        <button
          v-for="background in selectableBackgrounds"
          :key="background.id"
          class="background-option"
          :class="{ 'is-active': background.url === backgroundStore.activeBackgroundUrl }"
          type="button"
          @click="selectBackground(background.id)"
        >
          <span class="background-swatch" :style="previewStyle(background)" aria-hidden="true" />
          <span>{{ background.name }}</span>
        </button>
      </div>

      <el-input v-model="manualBackgroundUrl" placeholder="粘贴背景图片 URL" clearable />
      <div class="background-switcher-actions">
        <el-button size="small" :icon="RefreshCw" @click="backgroundStore.loadBackgrounds()">刷新</el-button>
        <el-button size="small" @click="backgroundStore.useDefaultBackground()">默认背景</el-button>
        <el-button size="small" type="primary" :disabled="!manualBackgroundUrl.trim()" @click="setManualBackground">
          应用
        </el-button>
      </div>
    </div>
    <template #reference>
      <button class="status-pill background-quick-switch" type="button" :title="backgroundStore.activeBackgroundName">
        <ImageIcon :size="16" aria-hidden="true" />
        <span>背景</span>
      </button>
    </template>
  </el-popover>
</template>
