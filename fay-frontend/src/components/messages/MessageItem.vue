<script setup lang="ts">
import { computed } from 'vue';
import { Check, X } from '@lucide/vue';
import type { MessageRecord } from '../../types';
import { parseAssistantContent, renderMarkdownContent } from '../../utils/messageContent';

const props = defineProps<{
  message: MessageRecord;
  index: number;
  shareSelectMode: boolean;
  renderVersion: number;
}>();

const emit = defineEmits<{
  (name: 'toggle-share', index: number): void;
  (name: 'toggle-adopt', message: MessageRecord): void;
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
const messageImages = computed(() => (Array.isArray(props.message.images) ? props.message.images : []));

function emitShareToggle() {
  emit('toggle-share', props.index);
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
      :src="message.type === 'fay' ? '/static/images/Fay_send.png' : '/static/images/User_send.png'"
      alt=""
    />
    <div class="bubble">
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
        <img v-for="image in messageImages" :key="image" :src="image" class="message-image" alt="消息图片" />
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
      <button
        v-if="message.type === 'fay' && message.id"
        class="adopt-action"
        type="button"
        @click="emit('toggle-adopt', message)"
      >
        <Check v-if="message.is_adopted" :size="16" />
        <X v-else :size="16" />
        {{ message.is_adopted ? '已采纳' : '采纳' }}
      </button>
    </div>
  </article>
</template>
