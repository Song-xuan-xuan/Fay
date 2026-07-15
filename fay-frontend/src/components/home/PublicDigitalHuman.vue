<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import type { PublicDigitalHuman } from '../../api/publicHomepage';
import { HOME_ASSETS } from '../../config/homeContent';

interface Props {
  human: PublicDigitalHuman;
  showStatus?: boolean;
}

const props = withDefaults(defineProps<Props>(), { showStatus: true });
const emit = defineEmits<{ greet: [] }>();
const renderFailed = ref(false);
const renderAvailable = ref(false);
const coverFailed = ref(false);
const canRender = computed(() => renderAvailable.value && !renderFailed.value);
const cover = computed(() => coverFailed.value ? HOME_ASSETS.localHumanCover : (props.human.cover_url || HOME_ASSETS.defaultHumanCover));

async function probeRenderer() {
  renderAvailable.value = false;
  renderFailed.value = false;
  if (props.human.type !== 'live2d' || !props.human.render_url) return;
  try {
    await fetch(props.human.render_url, { mode: 'no-cors' });
    renderAvailable.value = true;
  } catch {
    renderFailed.value = true;
  }
}

watch(() => props.human.render_url, probeRenderer, { immediate: true });
</script>

<template>
  <button class="public-human" type="button" aria-label="让数字人向你问好" @click="emit('greet')">
    <iframe v-if="canRender" :src="human.render_url" title="当前景区数字人" @error="renderFailed = true" />
    <img v-else :src="cover" :alt="`${human.name || '景区'}数字人`" @error="coverFailed = true" />
    <span v-if="showStatus" class="public-human-status"><i /> {{ human.name || '数字导览员' }} · ONLINE</span>
  </button>
</template>
