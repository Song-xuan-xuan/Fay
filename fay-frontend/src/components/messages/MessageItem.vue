<script setup lang="ts">
import { computed, ref } from 'vue';
import type { MessageRecord } from '../../types';
import { parseAssistantContent, renderMarkdownContent } from '../../utils/messageContent';

const props = defineProps<{
  message: MessageRecord;
  index: number;
  shareSelectMode: boolean;
  renderVersion: number;
  userAvatar?: string;
}>();

const emit = defineEmits<{
  (name: 'toggle-share', index: number): void;
  (name: 'toggle-think', message: MessageRecord): void;
  (name: 'toggle-prestart', message: MessageRecord): void;
  (name: 'content-click', mouseEvent: MouseEvent): void;
}>();

const parsedContent = computed(() => parseAssistantContent(props.message.content));
const renderedMainContent = computed(() => (
  renderMarkdownContent(parsedContent.value.mainContent || props.message.content, undefined, props.renderVersion)
));
const renderedPrestartContent = computed(() => (
  renderMarkdownContent(parsedContent.value.prestartContent, undefined, props.renderVersion)
));
const failedImages = ref(new Set<string>());
const messageImages = computed(() => (
  (Array.isArray(props.message.images) ? props.message.images : [])
    .map(normalizeMessageImageSrc)
    .filter((src): src is string => Boolean(src))
));
const avatarSrc = computed(() => (
  props.message.type === 'fay'
    ? '/static/images/Fay_send.png'
    : props.userAvatar || '/static/images/User_send.png'
));

function normalizeMessageImageSrc(image: unknown) {
  const raw = typeof image === 'string' ? image : '';
  const src = raw.trim().replace(/\\/g, '/');
  if (!src) return '';
  if (/^(https?:|data:image\/|blob:|\/)/.test(src)) return src;
  if (/^[^/]+\/\d{4}-\d{2}-\d{2}\/[^/]+$/.test(src)) {
    return `/api/get-image/${src}`;
  }
  return src;
}

function emitShareToggle() {
  emit('toggle-share', props.index);
}

function markImageFailed(src: string) {
  failedImages.value = new Set([...failedImages.value, src]);
}

function isImageFailed(src: string) {
  return failedImages.value.has(src);
}
</script>

<template>
  <article
    class="message-row"
    :class="[message.type === 'fay' ? 'from-fay' : 'from-user', { selected: message.shareSelected }]"
    @click="emitShareToggle"
  >
    <span v-if="shareSelectMode" class="share-check" :class="{ checked: message.shareSelected }"></span>
    <img
      class="avatar"
      :src="avatarSrc"
      alt=""
    />
    <div class="message-bubble">
      <button
        v-if="message.type === 'fay' && parsedContent.thinkContent"
        class="fold-button"
        type="button"
        @click="emit('toggle-think', message)"
      >
        思考过程
      </button>
      <pre v-if="message.thinkExpanded" class="think-block">{{ parsedContent.thinkContent }}</pre>
      <div class="markdown-body" @click="emit('content-click', $event)" v-html="renderedMainContent"></div>
      <div v-if="messageImages.length" class="message-images">
        <template v-for="(image, imageIndex) in messageImages" :key="`${image}-${imageIndex}`">
          <div v-if="isImageFailed(image)" class="message-image message-image-fallback" role="img" aria-label="图片加载失败">
            加载失败
          </div>
          <img v-else :src="image" class="message-image" alt="" loading="lazy" @error="markImageFailed(image)" />
        </template>
      </div>
      <button
        v-if="message.type === 'fay' && parsedContent.prestartContent"
        class="fold-button"
        type="button"
        @click="emit('toggle-prestart', message)"
      >
        预启动工具
      </button>
      <div
        v-if="message.prestartExpanded"
        class="prestart-block markdown-body"
        @click="emit('content-click', $event)"
        v-html="renderedPrestartContent"
      ></div>
      <time>{{ message.timetext }}</time>
    </div>
  </article>
</template>
