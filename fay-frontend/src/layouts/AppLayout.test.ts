import { describe, expect, it } from 'vitest';
import source from './AppLayout.vue?raw';

describe('AppLayout sidebar account menu', () => {
  it('groups profile and logout actions into one account settings menu', () => {
    expect(source).toContain('<el-dropdown');
    expect(source).toContain('command="profile"');
    expect(source).toContain('command="logout"');
    expect(source).toContain('账户设置');
    expect(source).not.toContain('logout-action');
  });

  it('does not expose the legacy persona page as a primary sidebar item', () => {
    expect(source).not.toContain("to: '/setting'");
    expect(source).not.toContain("label: '人设'");
  });
});
