import { computed, ref } from 'vue';
import { defineStore } from 'pinia';
import {
  changePassword as changePasswordApi,
  getCurrentUser,
  login as loginApi,
  logout as logoutApi,
  register as registerApi,
  uploadAvatar as uploadAvatarApi,
} from '../api/auth';
import type { AuthUser, LoginResponse } from '../types/auth';

const TOKEN_KEY = 'fay_token';
const USER_KEY = 'fay_user';

function readStoredUser(): AuthUser | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) as AuthUser : null;
  } catch {
    return null;
  }
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem(TOKEN_KEY) || '');
  const user = ref<AuthUser | null>(readStoredUser());
  const isAuthenticated = computed(() => Boolean(token.value && user.value));
  const isAdmin = computed(() => user.value?.role === 'admin');

  function persist(nextToken: string, nextUser: AuthUser) {
    token.value = nextToken;
    user.value = nextUser;
    localStorage.setItem('fay_token', nextToken);
    localStorage.setItem(USER_KEY, JSON.stringify(nextUser));
  }

  async function login(username: string, password: string) {
    const result = await loginApi({ username, password });
    persist(result.token, result);
    return result;
  }

  async function register(username: string, password: string, email = '') {
    const result = await registerApi({ username, password, email });
    persist(result.token, result);
    return result;
  }

  async function refreshUser() {
    if (!token.value) return null;
    const current = await getCurrentUser();
    user.value = current;
    localStorage.setItem(USER_KEY, JSON.stringify(current));
    return current;
  }

  async function changePassword(old_password: string, new_password: string) {
    const result = await changePasswordApi({ old_password, new_password });
    if (result.token && user.value) {
      persist(result.token, { ...user.value, must_change_password: false });
    }
    await refreshUser();
    return result;
  }

  async function uploadAvatar(file: File) {
    const result = await uploadAvatarApi(file);
    if (user.value) {
      user.value = { ...user.value, avatar_path: result.avatar_path };
      localStorage.setItem(USER_KEY, JSON.stringify(user.value));
    }
    await refreshUser();
    return result;
  }

  function clearSession() {
    token.value = '';
    user.value = null;
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  async function logout() {
    try {
      if (token.value) await logoutApi();
    } finally {
      clearSession();
    }
  }

  function restoreSession(payload: LoginResponse) {
    persist(payload.token, payload);
  }

  return {
    token,
    user,
    isAuthenticated,
    isAdmin,
    login,
    register,
    logout,
    refreshUser,
    changePassword,
    uploadAvatar,
    clearSession,
    restoreSession,
  };
});
