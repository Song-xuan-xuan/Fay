<script setup lang="ts">
import type { MessageRecord } from '../../types';
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
    @update:model-value="updateVisible"
  >
    <div id="sharePreviewContainer" class="share-preview-card">
      <header>Fay 开源数字人</header>
      <article
        v-for="message in messages"
        :key="`share-${message.type}-${message.id || message.timetext || message.content}`"
        class="share-preview-message"
        :class="message.type === 'fay' ? 'from-fay' : 'from-user'"
      >
        <strong>{{ message.type === 'fay' ? 'Fay' : username }}</strong>
        <div class="markdown-body" v-html="renderShareContent(message)"></div>
        <time>{{ message.timetext }}</time>
      </article>
      <footer>github.com/xszyou/fay | gitee.com/xszyou/fay</footer>
    </div>
    <template #footer>
      <el-button @click="updateVisible(false)">关闭</el-button>
      <el-button type="primary" :loading="exporting" @click="emit('download')">保存图片</el-button>
    </template>
  </el-dialog>
</template>
