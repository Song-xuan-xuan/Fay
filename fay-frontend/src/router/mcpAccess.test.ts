import { describe, expect, it } from 'vitest';
import appLayoutSource from '../layouts/AppLayout.vue?raw';
import routerSource from './index.ts?raw';

describe('MCP hidden admin access', () => {
  it('keeps MCP settings as an authenticated admin route', () => {
    expect(routerSource).toContain("path: 'settings'");
    expect(routerSource).toContain("name: 'mcp'");
    expect(routerSource).toContain("meta: { requiresAuth: true, requiresRole: 'admin' }");
    expect(routerSource).toContain("path: '/mcp', redirect: '/app/settings'");
  });

  it('does not expose MCP in the sidebar navigation', () => {
    expect(appLayoutSource).not.toContain("label: 'MCP'");
    expect(appLayoutSource).not.toContain('label: "MCP"');
  });
});
