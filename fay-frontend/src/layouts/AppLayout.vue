<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router';
import {
  BookOpen,
  Bot,
  LayoutDashboard,
  LogOut,
  MessageSquareText,
  MonitorCog,
  PanelLeftClose,
  PanelLeftOpen,
  Settings,
  UserCog,
} from '@lucide/vue';
import ProfileDialog from '../components/auth/ProfileDialog.vue';
import { useAppStore } from '../stores/app';
import { useAuthStore } from '../stores/auth';
import { ReconnectingSocket, getFayWebSocketUrl } from '../utils/websocket';
import { isNavItemActive } from '../utils/navigation';

const appStore = useAppStore();
const authStore = useAuthStore();
const route = useRoute();
const router = useRouter();
const sidebarCollapsed = ref(false);
const profileDialogVisible = ref(false);

const navItems = [
  { to: '/', label: '消息', icon: MessageSquareText, exact: true },
  { to: '/setting', label: '人设', icon: Settings, exact: false, requiresRole: 'admin' },
  { to: '/live2d', label: '数字人', icon: Bot, exact: false, requiresRole: 'admin' },
  { to: '/dashboard', label: '数据看板', icon: LayoutDashboard, exact: false },
  { to: '/knowledge', label: '知识库', icon: BookOpen, exact: false, requiresRole: 'admin' },
  { to: '/mcp', label: 'MCP', icon: MonitorCog, exact: false, requiresRole: 'admin' },
  { to: '/users', label: '用户', icon: UserCog, exact: false, requiresRole: 'admin' },
];
const logoSrc = '/static/images/Logo.png';
const defaultUserAvatar = '/static/images/User_send.png';
const visibleNavItems = computed(() => navItems.filter((item) => !item.requiresRole || (item.requiresRole === 'admin' && authStore.isAdmin)));

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
const operatorName = computed(() => authStore.user?.username || appStore.selectedUser?.[1] || 'User');
const operatorAvatar = computed(() => authStore.user?.avatar_path || defaultUserAvatar);

async function handleLogout() {
  await authStore.logout();
  await router.push({ name: 'login' });
}

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value;
}

function openProfileDialog() {
  profileDialogVisible.value = true;
}

onMounted(async () => {
  await authStore.refreshUser().catch(() => undefined);
  await Promise.allSettled([
    appStore.loadUsers(),
    appStore.loadBootstrapData(),
    appStore.refreshAudioConfig(),
  ]);
  appStore.refreshSystemStatus().catch(() => undefined);
  statusTimer = window.setInterval(() => {
    appStore.refreshSystemStatus().catch(() => undefined);
  }, 3000);

  socket = new ReconnectingSocket(getFayWebSocketUrl(), appStore.receiveWebsocketPayload, 5000, () => authStore.token);
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
  <div class="shell" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
    <aside class="sidebar" aria-label="主导航">
      <div class="brand">
        <img class="brand-logo" :src="logoSrc" alt="Fay" />
        <button
          class="sidebar-toggle"
          type="button"
          :aria-label="sidebarCollapsed ? '展开侧边栏' : '折叠侧边栏'"
          :title="sidebarCollapsed ? '展开侧边栏' : '折叠侧边栏'"
          @click="toggleSidebar"
        >
          <PanelLeftOpen v-if="sidebarCollapsed" :size="18" aria-hidden="true" />
          <PanelLeftClose v-else :size="18" aria-hidden="true" />
        </button>
      </div>

      <nav class="nav-list">
        <RouterLink
          v-for="item in visibleNavItems"
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
        <button class="operator" type="button" aria-label="个人中心" title="个人中心" @click="openProfileDialog">
          <img class="operator-avatar" :src="operatorAvatar" alt="" />
          <span>{{ operatorName }}</span>
        </button>
        <button class="logout-action" type="button" @click="handleLogout">
          <LogOut :size="18" aria-hidden="true" />
          <span>退出</span>
        </button>
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
    <ProfileDialog v-model:visible="profileDialogVisible" />
  </div>
</template>
