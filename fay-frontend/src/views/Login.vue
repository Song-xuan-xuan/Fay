<script setup lang="ts">
import { computed, reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { LogIn, UserPlus } from '@lucide/vue';
import { useAuthStore } from '../stores/auth';

type AuthMode = 'login' | 'register';

const authStore = useAuthStore();
const router = useRouter();
const route = useRoute();
const loading = ref(false);
const authMode = ref<AuthMode>('login');
const loginForm = reactive({ username: '', password: '' });
const registerForm = reactive({ username: '', password: '', confirmPassword: '', email: '' });

const submitText = computed(() => (authMode.value === 'login' ? '登录' : '注册账号'));
const submitIcon = computed(() => (authMode.value === 'login' ? LogIn : UserPlus));

function redirectAfterLogin() {
  const target = typeof route.query.redirect === 'string' ? route.query.redirect : '/';
  router.replace(target || '/');
}

function switchMode(mode: AuthMode) {
  authMode.value = mode;
}

async function submitLogin() {
  if (!loginForm.username.trim() || !loginForm.password) {
    ElMessage.error('请输入用户名和密码');
    return;
  }
  await authStore.login(loginForm.username.trim(), loginForm.password);
  redirectAfterLogin();
}

async function submitRegister() {
  const username = registerForm.username.trim();
  if (!username || !registerForm.password) {
    ElMessage.error('请输入用户名和密码');
    return;
  }
  if (registerForm.password !== registerForm.confirmPassword) {
    ElMessage.error('两次输入的新密码不一致');
    return;
  }
  await authStore.register(username, registerForm.password, registerForm.email.trim());
  ElMessage.success('注册成功');
  redirectAfterLogin();
}

async function submitAuth() {
  loading.value = true;
  try {
    if (authMode.value === 'login') {
      await submitLogin();
    } else {
      await submitRegister();
    }
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <main class="auth-gate">
    <div class="auth-home-preview" aria-hidden="true">
      <aside class="auth-preview-sidebar">
        <div class="auth-preview-logo" />
        <span class="active" />
        <span />
        <span />
        <span />
      </aside>
      <section class="auth-preview-workspace">
        <header class="auth-preview-topbar">
          <span />
          <span />
          <span />
        </header>
        <div class="auth-preview-content">
          <section class="auth-preview-user-list">
            <span />
            <span class="active" />
            <span />
          </section>
          <section class="auth-preview-chat">
            <span class="auth-preview-bubble left" />
            <span class="auth-preview-bubble right" />
            <span class="auth-preview-bubble left short" />
            <div class="auth-preview-composer" />
          </section>
          <section class="auth-preview-digital-human" />
        </div>
      </section>
    </div>
    <div class="auth-backdrop" aria-hidden="true" />
    <section class="auth-modal" role="dialog" aria-labelledby="auth-title" aria-modal="true">
      <div class="auth-title">
        <p class="eyebrow">Fay Console</p>
        <h1 id="auth-title">{{ authMode === 'login' ? '登录' : '注册' }}</h1>
        <p class="auth-subtitle">登录后才能使用数字人管理台</p>
      </div>

      <div class="auth-mode-tabs" role="tablist" aria-label="认证方式">
        <button type="button" :class="{ active: authMode === 'login' }" @click="switchMode('login')">登录</button>
        <button type="button" :class="{ active: authMode === 'register' }" @click="switchMode('register')">注册</button>
      </div>

      <el-form v-if="authMode === 'login'" label-position="top" @submit.prevent="submitAuth">
        <el-form-item label="用户名">
          <el-input v-model="loginForm.username" autocomplete="username" autofocus />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="loginForm.password" type="password" show-password autocomplete="current-password" />
        </el-form-item>
        <el-button class="login-submit" type="primary" :icon="submitIcon" :loading="loading" @click="submitAuth">
          {{ submitText }}
        </el-button>
      </el-form>

      <el-form v-else label-position="top" @submit.prevent="submitAuth">
        <el-form-item label="用户名">
          <el-input v-model="registerForm.username" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="registerForm.password" type="password" show-password autocomplete="new-password" />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input v-model="registerForm.confirmPassword" type="password" show-password autocomplete="new-password" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="registerForm.email" autocomplete="email" />
        </el-form-item>
        <el-button class="login-submit" type="primary" :icon="submitIcon" :loading="loading" @click="submitAuth">
          {{ submitText }}
        </el-button>
      </el-form>
    </section>
  </main>
</template>
