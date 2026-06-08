import { defineStore } from 'pinia';
import { computed, ref } from 'vue';
import { getAudioConfig, getChatSessions, getMemberList, getSystemStatus, type ChatSession } from '../api/message';
import { getData, getRunStatus, startLive as startLiveApi, stopLive as stopLiveApi, submitConfig } from '../api/setting';
import type { LiveState, MessageRecord, SystemStatus, UserRecord, VoiceOption, WebsocketPayload } from '../types';
import { buildAudioConfigPatch, toggleAudioFlag, type AudioConfig } from '../utils/audioControls';
import { useAuthStore } from './auth';
import { useLive2dStore } from './live2d';

function normalizeVoice(voice: VoiceOption) {
  return {
    value: voice.value || voice.id || '',
    label: voice.label || voice.name || voice.id || '',
  };
}

export const useAppStore = defineStore('app', () => {
  const authStore = useAuthStore();
  const users = ref<UserRecord[]>([]);
  const selectedUser = ref<UserRecord | null>(null);
  const liveState = ref<LiveState>(0);
  const configEditable = computed(() => liveState.value === 0);
  const voiceList = ref<Array<{ value: string; label: string }>>([]);
  const systemStatus = ref<SystemStatus>({ server: false, digital_human: false, remote_audio: false });
  const audioConfig = ref({ mic: false, speaker: false });
  const panelMsg = ref('');
  const latestPanelReply = ref<MessageRecord | null>(null);
  const panelReplySeq = ref(0);
  const sessions = ref<ChatSession[]>([]);
  const selectedSession = ref<ChatSession | null>(null);

  function ownUserRecord() {
    const current = authStore.user;
    return current ? [current.uid, current.username, current.avatar_path || ''] as UserRecord : null;
  }

  function syncSelectedUser() {
    const ownUser = ownUserRecord();
    if (ownUser && !authStore.isAdmin) {
      users.value = [ownUser];
      selectedUser.value = ownUser;
      return;
    }
    if (!selectedUser.value && users.value.length > 0) {
      selectedUser.value = users.value[0];
    }
  }

  async function loadUsers() {
    users.value = await getMemberList();
    syncSelectedUser();
  }

  function setSelectedSession(session: ChatSession | null) {
    selectedSession.value = session;
  }

  async function loadSessions(username?: string) {
    sessions.value = await getChatSessions(username);
    if (selectedSession.value) {
      selectedSession.value = sessions.value.find((item) => item.id === selectedSession.value?.id) || null;
    }
    if (!selectedSession.value && sessions.value.length > 0) {
      selectedSession.value = sessions.value[0];
    }
    return sessions.value;
  }

  async function loadBootstrapData() {
    const [status, data] = await Promise.all([getRunStatus(), getData()]);
    liveState.value = status.status ? 1 : 0;
    voiceList.value = (data.voice_list || []).map(normalizeVoice);
    const digitalHumans = data.config?.digital_humans;
    if (digitalHumans?.items?.length) {
      const live2d = useLive2dStore();
      live2d.items = digitalHumans.items;
      live2d.activeId = digitalHumans.active_id || '';
      if (live2d.activeHuman?.render_url) {
        live2d.iframeUrl = live2d.activeHuman.render_url;
      }
    }
  }

  async function refreshSystemStatus() {
    const username = selectedUser.value?.[1] || authStore.user?.username || '';
    systemStatus.value = await getSystemStatus(username);
  }

  async function refreshAudioConfig() {
    audioConfig.value = await getAudioConfig();
  }

  async function toggleAudioConfig(key: keyof AudioConfig) {
    const previous = audioConfig.value;
    const next = toggleAudioFlag(previous, key);
    audioConfig.value = next;
    try {
      await submitConfig(buildAudioConfigPatch({ [key]: next[key] }));
    } catch (error) {
      audioConfig.value = previous;
      throw error;
    }
  }

  async function startLive() {
    liveState.value = 2;
    await startLiveApi();
    liveState.value = 1;
  }

  async function stopLive() {
    liveState.value = 3;
    await stopLiveApi();
    liveState.value = 0;
  }

  function receiveWebsocketPayload(payload: WebsocketPayload) {
    if (payload.liveState !== undefined) {
      liveState.value = payload.liveState;
    }
    if (payload.panelMsg !== undefined) {
      panelMsg.value = payload.panelMsg;
    }
    if (payload.voiceList !== undefined) {
      voiceList.value = payload.voiceList.map(normalizeVoice);
    }
    if (payload.digitalHuman !== undefined) {
      useLive2dStore().receiveDigitalHuman(payload.digitalHuman, payload.digitalHumanActiveId);
    }
    if (payload.panelReply !== undefined) {
      const username = payload.panelReply.username;
      if (!authStore.isAdmin && username !== authStore.user?.username) {
        return;
      }
      latestPanelReply.value = payload.panelReply;
      panelReplySeq.value += 1;
      const uid = payload.panelReply.uid || Date.now();
      if (username && !users.value.some((user) => user[1] === username)) {
        users.value.push([uid, username, ''] as UserRecord);
      }
    }
  }

  return {
    users,
    selectedUser,
    liveState,
    configEditable,
    voiceList,
    systemStatus,
    audioConfig,
    panelMsg,
    latestPanelReply,
    panelReplySeq,
    sessions,
    selectedSession,
    loadUsers,
    loadSessions,
    setSelectedSession,
    loadBootstrapData,
    refreshSystemStatus,
    refreshAudioConfig,
    toggleAudioConfig,
    startLive,
    stopLive,
    receiveWebsocketPayload,
  };
});
