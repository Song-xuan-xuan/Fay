import { computed } from 'vue';
import { useAuthStore } from '../stores/auth';

export function useAuth() {
  const authStore = useAuthStore();

  return {
    user: computed(() => authStore.user),
    token: computed(() => authStore.token),
    isAuthenticated: computed(() => authStore.isAuthenticated),
    isAdmin: computed(() => authStore.isAdmin),
    login: authStore.login,
    logout: authStore.logout,
    changePassword: authStore.changePassword,
    refreshUser: authStore.refreshUser,
  };
}
