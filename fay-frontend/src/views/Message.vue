<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Image as ImageIcon } from '@lucide/vue';
import { addUser, adoptMessage, deleteUser, getMessageHistory, openImage, unadoptMessage } from '../api/message';
import type { MessageRecord, UserRecord } from '../types';
import { useAppStore } from '../stores/app';
import ChatComposer from '../components/messages/ChatComposer.vue';
import MessageList from '../components/messages/MessageList.vue';
import SharePreviewDialog from '../components/messages/SharePreviewDialog.vue';
import ShareToolbar from '../components/messages/ShareToolbar.vue';
import DigitalHumanPanel from '../components/messages/DigitalHumanPanel.vue';
import UserInfoDialog from '../components/messages/UserInfoDialog.vue';
import UserPanel from '../components/messages/UserPanel.vue';
import { useAudioControlActions } from '../composables/useAudioControlActions';
import { useMessageSubmit } from '../composables/useMessageSubmit';
import { useUserInfoEditor } from '../composables/useUserInfoEditor';
import { getImagePathFromClickTarget } from '../utils/messageContent';
import { loadMarked } from '../utils/markdown';
import { mergePanelReply } from '../utils/messageStream';
import { createShareImageFilename, exportElementAsImage } from '../utils/shareImage';
import { clearShareSelection, getShareSelectedMessages, selectAllShareMessages, toggleShareMessage } from '../utils/shareSelection';
const appStore = useAppStore();
const messages = ref<MessageRecord[]>([]);
const newMessage = ref('');
const loading = ref(false);
const hasMore = ref(false);
const offset = ref(0);
const limit = 30;
const newUsername = ref('');
const shareSelectMode = ref(false);
const sharePreviewVisible = ref(false);
const sharePreviewDialog = ref<InstanceType<typeof SharePreviewDialog> | null>(null);
const messageList = ref<InstanceType<typeof MessageList> | null>(null);
const shareExporting = ref(false);
const renderVersion = ref(0);
const chatComposer = ref<InstanceType<typeof ChatComposer> | null>(null);
const pendingImages = ref<File[]>([]);

const selectedUsername = computed(() => appStore.selectedUser?.[1] || 'User');
const canSend = computed(() => (newMessage.value.trim().length > 0 || pendingImages.value.length > 0) && appStore.liveState === 1);
const shareSelectedMessages = computed(() => getShareSelectedMessages(messages.value));
const userInfoEditor = useUserInfoEditor();
const audioActions = useAudioControlActions(appStore);
const { submitMessage } = useMessageSubmit({
  selectedUsername,
  newMessage,
  pendingImages,
  getLiveState: () => appStore.liveState,
  clearComposerImages: () => chatComposer.value?.clearImages(),
  reloadMessages: () => loadMessages(true),
});

function scrollToBottom() {
  messageList.value?.scrollToBottom();
}

async function loadMessages(reset = true) {
  if (!appStore.selectedUser) {
    messages.value = [];
    return;
  }
  loading.value = true;
  try {
    const nextOffset = reset ? 0 : offset.value;
    const data = await getMessageHistory(selectedUsername.value, limit, nextOffset);
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

async function addNewUser() {
  const username = newUsername.value.trim();
  if (!username) {
    return;
  }
  const result = await addUser(username);
  if (result.success) {
    const user = [result.uid || Date.now(), username] as UserRecord;
    appStore.users.push(user);
    appStore.selectedUser = user;
    newUsername.value = '';
    await loadMessages();
  }
}

async function removeUser(user: UserRecord) {
  if (user[1] === 'User') {
    return;
  }
  await ElMessageBox.confirm(`确认删除用户 ${user[1]} 及其聊天记录？`, '删除用户', { type: 'warning' });
  await deleteUser(user[1]);
  appStore.users = appStore.users.filter((item) => item[1] !== user[1]);
  appStore.selectedUser = appStore.users[0] || null;
}

async function toggleAdopt(message: MessageRecord) {
  if (!message.id) {
    return;
  }
  const result = message.is_adopted ? await unadoptMessage(message.id) : await adoptMessage(message.id);
  if (result.status === 'success') {
    message.is_adopted = message.is_adopted ? 0 : 1;
    ElMessage.success(result.msg);
  } else {
    ElMessage.error(result.msg);
  }
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
  if (!shareSelectMode.value) {
    return;
  }
  messages.value = toggleShareMessage(messages.value, index);
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
  loadMessages();
});

watch(() => appStore.panelReplySeq, () => {
  if (!appStore.latestPanelReply) {
    return;
  }
  const next = mergePanelReply(messages.value, appStore.latestPanelReply, selectedUsername.value);
  if (next !== messages.value) {
    messages.value = next;
    scrollToBottom();
  }
});

onMounted(async () => {
  await loadMessages();
  refreshMarkdownRenderer();
});
</script>

<template>
  <section class="page-grid page-grid-message">
    <UserPanel
      v-model:new-username="newUsername"
      :users="appStore.users"
      :selected-user="appStore.selectedUser"
      @select="appStore.selectedUser = $event"
      @edit="userInfoEditor.openUserInfoDialog"
      @remove="removeUser"
      @add="addNewUser"
    />

    <section class="panel chat-panel">
      <div class="panel-header">
        <div>
          <h2>{{ selectedUsername === 'User' ? '主人' : selectedUsername }}</h2>
          <p>{{ appStore.panelMsg || '等待新的对话消息' }}</p>
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
        @load-more="loadMessages(false)"
        @toggle-share="toggleShareSelect"
        @toggle-adopt="toggleAdopt"
        @toggle-think="toggleThink"
        @toggle-prestart="togglePrestart"
        @content-click="openLocalImage"
      />

      <ChatComposer
        ref="chatComposer"
        v-model="newMessage"
        :can-send="canSend"
        :live-state="appStore.liveState" :mic-enabled="appStore.audioConfig.mic" :speaker-enabled="appStore.audioConfig.speaker"
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
    <UserInfoDialog
      v-model:visible="userInfoEditor.visible.value"
      v-model:extra-info="userInfoEditor.extraInfo.value"
      v-model:user-portrait="userInfoEditor.userPortrait.value"
      :loading="userInfoEditor.loading.value"
      :saving="userInfoEditor.saving.value"
      :user="userInfoEditor.editingUser.value"
      @save="userInfoEditor.saveUserInfo"
    />
  </section>
</template>
