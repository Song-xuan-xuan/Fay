<script setup lang="ts">
import type { MessageRecord } from '../../types';
import { BRAND_ASSISTANT_NAME, BRAND_SHARE_FOOTER, BRAND_SHARE_TITLE } from '../../config/brand';
import { parseAssistantContent, renderMarkdownContent } from '../../utils/messageContent';

const props = defineProps<{
  visible: boolean;
  messages: MessageRecord[];
  username: string;
  exporting: boolean;
  renderVersion: number;
}>();

const emit = defineEmits<{
  (event: 'update:visible', value: boolean): void;
  (event: 'download'): void;
}>();

function updateVisible(value: boolean) {
  emit('update:visible', value);
}

function getPreviewElement(): HTMLElement | null {
  return document.getElementById('sharePreviewContainer');
}

function renderShareContent(message: MessageRecord): string {
  const parsed = parseAssistantContent(message.content);
  return renderMarkdownContent(parsed.mainContent || message.content, undefined, props.renderVersion);
}

defineExpose({ getPreviewElement });
</script>

<template>
  <el-dialog
    :model-value="visible"
    title="分享图预览"
    width="560px"
    append-to-body
    @update:model-value="updateVisible"
  >
    <div id="sharePreviewContainer" class="share-preview-card">
      <header>{{ BRAND_SHARE_TITLE }}</header>
      <article
        v-for="message in messages"
        :key="`share-${message.type}-${message.id || message.timetext || message.content}`"
        class="share-preview-message"
        :class="message.type === 'fay' ? 'from-fay' : 'from-user'"
      >
        <strong>{{ message.type === 'fay' ? BRAND_ASSISTANT_NAME : username }}</strong>
        <div class="markdown-body" v-html="renderShareContent(message)"></div>
        <time>{{ message.timetext }}</time>
      </article>
      <footer>{{ BRAND_SHARE_FOOTER }}</footer>
    </div>
    <template #footer>
      <el-button @click="updateVisible(false)">关闭</el-button>
      <el-button type="primary" :loading="exporting" @click="emit('download')">保存图片</el-button>
    </template>
  </el-dialog>
</template>
