import { describe, expect, it } from 'vitest';
import guardSource from './guards.ts?raw';
import routerSource from './index.ts?raw';
import loginSource from '../views/Login.vue?raw';

describe('public homepage route migration', () => {
  it('serves the homepage publicly and mounts authenticated pages below /app', () => {
    expect(routerSource).toContain("path: '/',");
    expect(routerSource).toContain('component: AppLayout');
    expect(routerSource).toContain("path: '', name: 'home', component: Home");
    expect(routerSource).toContain("meta: { requiresAuth: false, public: true }");
    expect(routerSource).toContain("path: '/app'");
    expect(routerSource).toContain("path: 'chat', name: 'message'");
  });

  it('keeps legacy business URLs as redirects to the protected workspace', () => {
    expect(routerSource).toContain("path: '/live2d', redirect: '/app/live2d'");
    expect(routerSource).toContain("path: '/dashboard', redirect: '/app/dashboard'");
    expect(routerSource).toContain("path: '/recommendation', redirect: '/app/recommendation'");
    expect(routerSource).toContain("path: '/knowledge', redirect: '/app/knowledge'");
    expect(routerSource).toContain("path: '/mcp', redirect: '/app/settings'");
  });

  it('uses the public homepage as the default post-login destination', () => {
    expect(guardSource).toContain("authStore.isAuthenticated ? { name: 'home' } : true");
    expect(loginSource).toContain("route.query.redirect : '/'");
    expect(loginSource).toContain("target || '/'");
  });
});
