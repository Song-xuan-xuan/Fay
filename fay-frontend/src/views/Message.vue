<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { ElMessage } from 'element-plus';
import { Image as ImageIcon } from '@lucide/vue';
import { getMessageHistory, openImage } from '../api/message';
import type { MessageRecord } from '../types';
import { useAppStore } from '../stores/app';
import { useAuthStore } from '../stores/auth';
import ChatComposer from '../components/messages/ChatComposer.vue';
import DigitalHumanPanel from '../components/messages/DigitalHumanPanel.vue';
import MessageList from '../components/messages/MessageList.vue';
import SessionPanel from '../components/messages/SessionPanel.vue';
import SharePreviewDialog from '../components/messages/SharePreviewDialog.vue';
import ShareToolbar from '../components/messages/ShareToolbar.vue';
import { useAudioControlActions } from '../composables/useAudioControlActions';
import { useChatSessions } from '../composables/useChatSessions';
import { useMessageSubmit } from '../composables/useMessageSubmit';
import { getImagePathFromClickTarget } from '../utils/messageContent';
import { loadMarked } from '../utils/markdown';
import { mergePanelReply } from '../utils/messageStream';
import { createShareImageFilename, exportElementAsImage } from '../utils/shareImage';
import { clearShareSelection, getShareSelectedMessages, selectAllShareMessages, toggleShareMessage } from '../utils/shareSelection';

const appStore = useAppStore();
const authStore = useAuthStore();
const messages = ref<MessageRecord[]>([]);
const newMessage = ref('');
const loading = ref(false);
const hasMore = ref(false);
const offset = ref(0);
const limit = 30;
const shareSelectMode = ref(false);
const sharePreviewVisible = ref(false);
const sharePreviewDialog = ref<InstanceType<typeof SharePreviewDialog> | null>(null);
const messageList = ref<InstanceType<typeof MessageList> | null>(null);
const shareExporting = ref(false);
const renderVersion = ref(0);
const chatComposer = ref<InstanceType<typeof ChatComposer> | null>(null);
const pendingImages = ref<File[]>([]);

const selectedUsername = computed(() => (authStore.isAdmin ? appStore.selectedUser?.[1] || 'User' : authStore.user?.username || appStore.selectedUser?.[1] || 'User'));
const selectedUserAvatar = computed(() => {
  if (!authStore.isAdmin) {
    return authStore.user?.avatar_path || '';
  }
  if (appStore.selectedUser?.[1] === authStore.user?.username) {
    return authStore.user?.avatar_path || appStore.selectedUser?.[2] || '';
  }
  return appStore.selectedUser?.[2] || '';
});
const selectedSessionId = computed<number | null>(() => appStore.selectedSession?.id ?? null);
const canSend = computed(() => selectedSessionId.value !== null && (newMessage.value.trim().length > 0 || pendingImages.value.length > 0) && appStore.liveState === 1);
const canControlService = computed(() => authStore.isAdmin);
const shareSelectedMessages = computed(() => getShareSelectedMessages(messages.value));
const audioActions = useAudioControlActions(appStore);
const { submitMessage } = useMessageSubmit({
  selectedUsername,
  selectedSessionId,
  newMessage,
  pendingImages,
  getLiveState: () => appStore.liveState,
  clearComposerImages: () => chatComposer.value?.clearImages(),
  reloadMessages: () => loadMessages(true),
});
const {
  sessionLoading,
  reloadSessionsAndMessages,
  selectSession,
  createSession,
  renameSession,
  removeSession,
} = useChatSessions({ selectedUsername, loadMessages });

function scrollToBottom() {
  messageList.value?.scrollToBottom();
}

async function loadMessages(reset = true) {
  if (selectedSessionId.value === null) {
    messages.value = [];
    return;
  }
  loading.value = true;
  try {
    const nextOffset = reset ? 0 : offset.value;
    const data = await getMessageHistory(selectedUsername.value, limit, nextOffset, selectedSessionId.value);
    messages.value = reset ? data.list : [...data.list, ...messages.value];
    hasMore.value = data.hasMore;
    offset.value = messages.value.length;
    if (reset) {
      scrollToBottom();
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载消息失败');
  } finally {
    loading.value = false;
  }
}

function handleImagesChange(images: File[]) {
  pendingImages.value = images;
}

function enterShareSelectMode() {
  shareSelectMode.value = true;
  messages.value = clearShareSelection(messages.value);
}

function exitShareSelectMode() {
  shareSelectMode.value = false;
  sharePreviewVisible.value = false;
  messages.value = clearShareSelection(messages.value);
}

function toggleShareSelect(index: number) {
  if (shareSelectMode.value) {
    messages.value = toggleShareMessage(messages.value, index);
  }
}

function toggleThink(message: MessageRecord) {
  message.thinkExpanded = !message.thinkExpanded;
}

function togglePrestart(message: MessageRecord) {
  message.prestartExpanded = !message.prestartExpanded;
}

function previewShareImage() {
  if (shareSelectedMessages.value.length === 0) {
    ElMessage.warning('请先选择消息');
    return;
  }
  sharePreviewVisible.value = true;
}

async function downloadShareImage() {
  const previewElement = sharePreviewDialog.value?.getPreviewElement();
  if (!previewElement) {
    ElMessage.error('分享图预览未准备好');
    return;
  }
  shareExporting.value = true;
  try {
    await exportElementAsImage(previewElement, createShareImageFilename());
    ElMessage.success('分享图已保存');
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '生成图片失败，请尝试截图保存');
  } finally {
    shareExporting.value = false;
  }
}

async function openLocalImage(event: MouseEvent) {
  const imagePath = getImagePathFromClickTarget(event.target);
  if (!imagePath) {
    return;
  }
  try {
    const result = await openImage(imagePath);
    if (!result.success) {
      ElMessage.error(result.message || '打开图片失败');
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '打开图片失败');
  }
}

function refreshMarkdownRenderer() {
  loadMarked().then(() => {
    renderVersion.value += 1;
  }).catch(() => undefined);
}

watch(() => appStore.selectedUser, () => {
  appStore.setSelectedSession(null);
  reloadSessionsAndMessages();
});

watch(() => appStore.panelReplySeq, () => {
  if (!appStore.latestPanelReply) {
    return;
  }
  const next = mergePanelReply(messages.value, appStore.latestPanelReply, selectedUsername.value, selectedSessionId.value);
  if (next !== messages.value) {
    messages.value = next;
    scrollToBottom();
  }
});

onMounted(async () => {
  await reloadSessionsAndMessages();
  refreshMarkdownRenderer();
});
</script>

<template>
  <section class="page-grid page-grid-message">
    <SessionPanel
      :sessions="appStore.sessions"
      :selected-session="appStore.selectedSession"
      :loading="sessionLoading"
      @select="selectSession"
      @create="createSession"
      @rename="renameSession"
      @remove="removeSession"
    />

    <section class="panel chat-panel">
      <div class="panel-header">
        <div>
          <h2>{{ selectedUsername === 'User' ? '主人' : selectedUsername }}</h2>
          <p>{{ appStore.panelMsg || appStore.selectedSession?.title || '等待新的对话消息' }}</p>
        </div>
        <el-button :icon="ImageIcon" :disabled="messages.length === 0" @click="enterShareSelectMode">分享图</el-button>
      </div>

      <ShareToolbar
        v-if="shareSelectMode"
        :selected-count="shareSelectedMessages.length"
        @select-all="messages = selectAllShareMessages(messages)"
        @clear="messages = clearShareSelection(messages)"
        @preview="previewShareImage"
        @exit="exitShareSelectMode"
      />

      <MessageList
        ref="messageList"
        :messages="messages"
        :loading="loading"
        :has-more="hasMore"
        :share-select-mode="shareSelectMode"
        :render-version="renderVersion"
        :user-avatar="selectedUserAvatar"
        @load-more="loadMessages(false)"
        @toggle-share="toggleShareSelect"
        @toggle-think="toggleThink"
        @toggle-prestart="togglePrestart"
        @content-click="openLocalImage"
      />

      <ChatComposer
        ref="chatComposer"
        v-model="newMessage"
        :can-send="canSend"
        :live-state="appStore.liveState" :mic-enabled="appStore.audioConfig.mic" :speaker-enabled="appStore.audioConfig.speaker"
        :show-management-controls="canControlService"
        @submit="submitMessage" @toggle-mic="audioActions.toggleMic"
        @toggle-speaker="audioActions.toggleSpeaker" @start-live="audioActions.startLiveFromComposer"
        @images-change="handleImagesChange"
      />

      <SharePreviewDialog
        ref="sharePreviewDialog"
        v-model:visible="sharePreviewVisible"
        :messages="shareSelectedMessages"
        :username="selectedUsername"
        :exporting="shareExporting"
        :render-version="renderVersion"
        @download="downloadShareImage"
      />
    </section>

    <DigitalHumanPanel />
  </section>
</template>
