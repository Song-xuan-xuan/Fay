import type { ComputedRef } from 'vue';
import { ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import {
  createChatSession,
  deleteChatSession as deleteChatSessionApi,
  renameChatSession,
  type ChatSession,
} from '../api/message';
import { useAppStore } from '../stores/app';

interface ChatSessionOptions {
  selectedUsername: ComputedRef<string>;
  loadMessages: (reset?: boolean) => Promise<void>;
}

function isDialogCancel(error: unknown) {
  return error === 'cancel' || error === 'close';
}

export function useChatSessions(options: ChatSessionOptions) {
  const appStore = useAppStore();
  const sessionLoading = ref(false);

  async function ensureSession() {
    if (appStore.sessions.length > 0) {
      return;
    }
    const created = await createChatSession('新会话', options.selectedUsername.value);
    appStore.setSelectedSession(created.session);
    await appStore.loadSessions(options.selectedUsername.value);
  }

  async function loadSessionsForUser() {
    sessionLoading.value = true;
    try {
      await appStore.loadUsers();
      await appStore.loadSessions(options.selectedUsername.value);
      await ensureSession();
    } catch (error) {
      ElMessage.error(error instanceof Error ? error.message : '加载会话失败');
    } finally {
      sessionLoading.value = false;
    }
  }

  async function reloadSessionsAndMessages() {
    await loadSessionsForUser();
    await options.loadMessages(true);
  }

  function selectSession(session: ChatSession) {
    appStore.setSelectedSession(session);
    options.loadMessages(true);
  }

  async function createSession() {
    try {
      const { value } = await ElMessageBox.prompt('会话名称', '新建会话', { inputValue: '新会话' });
      const title = String(value || '').trim() || '新会话';
      const created = await createChatSession(title, options.selectedUsername.value);
      await appStore.loadSessions(options.selectedUsername.value);
      appStore.setSelectedSession(appStore.sessions.find((item) => item.id === created.session.id) || created.session);
      await options.loadMessages(true);
    } catch (error) {
      if (!isDialogCancel(error)) {
        ElMessage.error(error instanceof Error ? error.message : '创建会话失败');
      }
    }
  }

  async function renameSession(session: ChatSession) {
    if (session.id === 0) {
      return;
    }
    try {
      const { value } = await ElMessageBox.prompt('会话名称', '重命名会话', { inputValue: session.title || '未命名会话' });
      const title = String(value || '').trim();
      if (!title) {
        return;
      }
      const renamed = await renameChatSession(session.id, title);
      await appStore.loadSessions(options.selectedUsername.value);
      appStore.setSelectedSession(appStore.sessions.find((item) => item.id === renamed.session.id) || renamed.session);
    } catch (error) {
      if (!isDialogCancel(error)) {
        ElMessage.error(error instanceof Error ? error.message : '重命名会话失败');
      }
    }
  }

  async function removeSession(session: ChatSession) {
    try {
      await ElMessageBox.confirm(`确认永久删除「${session.title || '未命名会话'}」及其中全部消息？`, '删除会话', {
        type: 'warning',
        confirmButtonText: '永久删除',
        cancelButtonText: '取消',
      });
      await deleteChatSessionApi(session.id, options.selectedUsername.value);
      await reloadSessionsAndMessages();
      ElMessage.success('会话已删除');
    } catch (error) {
      if (!isDialogCancel(error)) {
        ElMessage.error(error instanceof Error ? error.message : '删除会话失败');
      }
    }
  }

  return {
    sessionLoading,
    loadSessionsForUser,
    reloadSessionsAndMessages,
    selectSession,
    createSession,
    renameSession,
    removeSession,
  };
}
