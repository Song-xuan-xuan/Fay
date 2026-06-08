import type { Router } from 'vue-router';
import { useAuthStore } from '../stores/auth';

async function ensureCurrentUser(authStore: ReturnType<typeof useAuthStore>) {
  if (!authStore.token) return false;
  if (!authStore.user) {
    await authStore.refreshUser();
  }
  return authStore.isAuthenticated;
}

export function setupAuthGuards(router: Router) {
  router.beforeEach(async (to) => {
    const authStore = useAuthStore();
    const requiresAuth = to.matched.some((record) => record.meta.requiresAuth !== false);
    const requiresRole = to.matched.find((record) => record.meta.requiresRole)?.meta.requiresRole;

    if (to.name === 'login') {
      return authStore.isAuthenticated ? { name: 'message' } : true;
    }
    if (requiresAuth && !(await ensureCurrentUser(authStore))) {
      return { name: 'login', query: { redirect: to.fullPath } };
    }
    if (requiresRole === 'admin' && !authStore.isAdmin) {
      return { name: 'message' };
    }
    return true;
  });
}
