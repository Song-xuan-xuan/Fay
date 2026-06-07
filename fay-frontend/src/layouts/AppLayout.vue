<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, watch } from 'vue';
import { RouterLink, RouterView, useRoute } from 'vue-router';
import { BookOpen, Bot, MessageSquareText, MonitorCog, Settings, UserRound } from '@lucide/vue';
import { useAppStore } from '../stores/app';
import { ReconnectingSocket, getFayWebSocketUrl } from '../utils/websocket';
import { isNavItemActive } from '../utils/navigation';

const appStore = useAppStore();
const route = useRoute();

const navItems = [
  { to: '/', label: '消息', icon: MessageSquareText, exact: true },
  { to: '/setting', label: '人设', icon: Settings, exact: false },
  { to: '/live2d', label: '数字人', icon: Bot, exact: false },
  { to: '/knowledge', label: '知识库', icon: BookOpen, exact: false },
  { to: '/mcp', label: 'MCP', icon: MonitorCog, exact: false },
];
const logoSrc = '/static/images/Logo.png';

let socket: ReconnectingSocket | null = null;
let statusTimer: number | null = null;

const liveStateText = computed(() => {
  const map = {
    0: '未开启',
    1: '运行中',
    2: '正在开启',
    3: '正在关闭',
  };
  return map[appStore.liveState] || '未知';
});

const selectedUsername = computed(() => appStore.selectedUser?.[1] || 'User');

onMounted(async () => {
  await Promise.allSettled([
    appStore.loadUsers(),
    appStore.loadBootstrapData(),
    appStore.refreshAudioConfig(),
  ]);
  appStore.refreshSystemStatus().catch(() => undefined);
  statusTimer = window.setInterval(() => {
    appStore.refreshSystemStatus().catch(() => undefined);
  }, 3000);

  socket = new ReconnectingSocket(getFayWebSocketUrl(), appStore.receiveWebsocketPayload);
  socket.connect();
  socket.registerUsername(selectedUsername.value);
});

watch(selectedUsername, (username) => {
  socket?.registerUsername(username);
});

onBeforeUnmount(() => {
  socket?.close();
  if (statusTimer !== null) {
    window.clearInterval(statusTimer);
  }
});
</script>

<template>
  <div class="shell">
    <aside class="sidebar" aria-label="主导航">
      <div class="brand">
        <img :src="logoSrc" alt="Fay" />
      </div>

      <nav class="nav-list">
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          :exact="item.to === '/'"
          class="nav-item"
          :class="{ 'is-active': isNavItemActive(route.path, item) }"
        >
          <component :is="item.icon" :size="20" aria-hidden="true" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div class="sidebar-footer">
        <div class="operator">
          <UserRound :size="18" aria-hidden="true" />
          <span>{{ appStore.selectedUser?.[1] || 'User' }}</span>
        </div>
      </div>
    </aside>

    <main class="workspace">
      <header class="topbar">
        <div>
          <p class="eyebrow">Fay Console</p>
          <h1>数字人管理台</h1>
        </div>
        <div class="status-strip" aria-label="系统状态">
          <span class="status-pill" :class="{ ok: appStore.systemStatus.server }">后端</span>
          <span class="status-pill" :class="{ ok: appStore.systemStatus.digital_human }">数字人</span>
          <span class="status-pill" :class="{ ok: appStore.systemStatus.remote_audio }">远程音频</span>
          <span class="status-pill live">{{ liveStateText }}</span>
        </div>
      </header>

      <RouterView />
    </main>
  </div>
</template>
