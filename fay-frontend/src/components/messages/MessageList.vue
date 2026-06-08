<script setup lang="ts">
import { nextTick, ref } from 'vue';
import type { MessageRecord } from '../../types';
import MessageItem from './MessageItem.vue';

defineProps<{
  messages: MessageRecord[];
  loading: boolean;
  hasMore: boolean;
  shareSelectMode: boolean;
  renderVersion: number;
  userAvatar?: string;
}>();

const emit = defineEmits<{
  (name: 'load-more'): void;
  (name: 'toggle-share', index: number): void;
  (name: 'toggle-think', message: MessageRecord): void;
  (name: 'toggle-prestart', message: MessageRecord): void;
  (name: 'content-click', mouseEvent: MouseEvent): void;
}>();

const chatBody = ref<HTMLElement | null>(null);

function scrollToBottom() {
  nextTick(() => {
    if (chatBody.value) {
      chatBody.value.scrollTop = chatBody.value.scrollHeight;
    }
  });
}

defineExpose({ scrollToBottom });
</script>

<template>
  <div ref="chatBody" class="chat-body">
    <button v-if="hasMore" type="button" class="load-more" @click="emit('load-more')">加载更早消息</button>
    <el-empty v-if="!messages.length && !loading" description="暂无消息" />
    <MessageItem
      v-for="(message, index) in messages"
      :key="`${message.type}-${message.id || message.timetext || message.content}`"
      :message="message"
      :index="index"
      :share-select-mode="shareSelectMode"
      :render-version="renderVersion"
      :user-avatar="userAvatar"
      @toggle-share="emit('toggle-share', $event)"
      @toggle-think="emit('toggle-think', $event)"
      @toggle-prestart="emit('toggle-prestart', $event)"
      @content-click="emit('content-click', $event)"
    />
  </div>
</template>
