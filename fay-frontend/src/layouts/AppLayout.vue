<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch, type CSSProperties, type Component } from 'vue';
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router';
import {
  AudioLines,
  BookOpen,
  Bot,
  ChevronDown,
  LayoutDashboard,
  LogOut,
  MessageSquareText,
  Route as RouteIcon,
  Settings,
  UserCog,
} from '@lucide/vue';
import ProfileDialog from '../components/auth/ProfileDialog.vue';
import BackgroundSwitcher from '../components/backgrounds/BackgroundSwitcher.vue';
import DigitalHumanPanel from '../components/messages/DigitalHumanPanel.vue';
import { BRAND_CONSOLE_EYEBROW, BRAND_CONSOLE_NAME, BRAND_NAME } from '../config/brand';
import { useAppStore } from '../stores/app';
import { useAuthStore } from '../stores/auth';
import { useBackgroundStore } from '../stores/background';
import { BRAND_LOGO_SRC, DEFAULT_USER_AVATAR_SRC } from '../utils/assets';
import type { DigitalHumanPanelContext } from '../utils/digitalHumanRenderUrl';
import { ReconnectingSocket, getFayWebSocketUrl } from '../utils/websocket';
import {
  getPrimaryNavigationGroups,
  isNavigationGroupActive,
  type PrimaryNavigationKey,
} from '../utils/navigationGroups';

const appStore = useAppStore();
const authStore = useAuthStore();
const backgroundStore = useBackgroundStore();
const route = useRoute();
const router = useRouter();
const profileDialogVisible = ref(false);

const navIcons: Record<PrimaryNavigationKey, Component> = {
  message: MessageSquareText,
  knowledge: BookOpen,
  'digital-human': Bot,
  recommendation: RouteIcon,
  data: LayoutDashboard,
  settings: Settings,
};

const primaryNavItems = getPrimaryNavigationGroups().map((item) => ({
  ...item,
  icon: navIcons[item.key],
}));
const visiblePrimaryNavItems = computed(() => primaryNavItems.filter((item) => !item.requiresRole || (item.requiresRole === 'admin' && authStore.isAdmin)));

const logoSrc = BRAND_LOGO_SRC;
const defaultUserAvatar = DEFAULT_USER_AVATAR_SRC;

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
const isMessageRoute = computed(() => route.name === 'message');
const digitalHumanContext = computed<DigitalHumanPanelContext>(() => route.name === 'message' ? 'message' : 'default');
const stageBackgroundStyle = computed<CSSProperties>(() => ({
  backgroundImage: `linear-gradient(90deg, rgba(69, 159, 226, 0.62), rgba(255, 255, 255, 0.1) 52%, rgba(255, 255, 255, 0.28)), url("${backgroundStore.activeBackgroundUrl.replace(/"/g, '\\"')}")`,
}));

async function handleLogout() {
  await authStore.logout();
  await router.push({ name: 'login' });
}

async function handleAccountCommand(command: string | number | object) {
  if (command === 'profile') {
    openProfileDialog();
    return;
  }
  if (command === 'logout') {
    await handleLogout();
  }
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
  <div class="immersive-shell" :class="{ 'is-message-route': isMessageRoute }">
    <div class="stage-background" :style="stageBackgroundStyle" aria-hidden="true" />
    <aside class="workspace-rail" aria-label="主导航">
      <div class="rail-brand">
        <img class="rail-logo" :src="logoSrc" :alt="BRAND_NAME" />
        <span>{{ BRAND_NAME }}</span>
      </div>

      <nav class="rail-nav">
        <RouterLink
          v-for="item in visiblePrimaryNavItems"
          :key="item.key"
          :to="item.to"
          class="rail-nav-item"
          :class="{ 'is-active': isNavigationGroupActive(route.path, item) }"
          :aria-label="item.label"
          :title="item.label"
        >
          <component :is="item.icon" :size="22" aria-hidden="true" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div class="rail-account">
        <el-dropdown trigger="click" placement="top-start" popper-class="account-menu-popper" @command="handleAccountCommand">
          <button class="account-trigger immersive-account-trigger" type="button" aria-label="账户设置" title="账户设置">
            <img class="account-avatar" :src="operatorAvatar" alt="" />
            <span class="account-copy">
              <strong>{{ operatorName }}</strong>
              <small>账户设置</small>
            </span>
            <ChevronDown class="account-chevron" :size="16" aria-hidden="true" />
          </button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">
                <UserCog :size="16" aria-hidden="true" />
                <span>个人设置</span>
              </el-dropdown-item>
              <el-dropdown-item command="logout" divided>
                <LogOut :size="16" aria-hidden="true" />
                <span>退出登录</span>
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </aside>

    <aside class="workspace-human-stage" aria-label="数字人展示">
      <div class="workspace-human-body">
        <DigitalHumanPanel :view-context="digitalHumanContext" />
        <div
          v-if="isMessageRoute"
          class="voice-orb"
          :class="{ active: appStore.audioConfig.mic }"
          aria-label="数字人语音状态"
          title="数字人语音状态"
        >
          <AudioLines :size="24" aria-hidden="true" />
        </div>
      </div>
    </aside>

    <main class="immersive-workspace">
      <header class="stage-topbar">
        <div class="stage-title">
          <p class="eyebrow">{{ BRAND_CONSOLE_EYEBROW }}</p>
          <h1>{{ BRAND_CONSOLE_NAME }}</h1>
        </div>
        <div class="stage-status-strip" aria-label="系统状态">
          <BackgroundSwitcher />
          <span class="status-pill" :class="{ ok: appStore.systemStatus.server }">后端</span>
          <span class="status-pill" :class="{ ok: appStore.systemStatus.digital_human }">数字人</span>
          <span class="status-pill" :class="{ ok: appStore.systemStatus.remote_audio }">远程音频</span>
          <span class="status-pill live">{{ liveStateText }}</span>
        </div>
      </header>

      <section class="stage-content">
        <RouterView />
      </section>
    </main>
    <ProfileDialog v-model:visible="profileDialogVisible" />
  </div>
</template>
