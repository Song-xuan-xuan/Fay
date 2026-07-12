import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import source from './AppLayout.vue?raw';

const layoutCss = readFileSync(new URL('../styles/layout.css', import.meta.url), 'utf-8');

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

  it('uses the immersive digital-human workspace shell', () => {
    expect(source).toContain('immersive-shell');
    expect(source).toContain('stage-background');
    expect(source).toContain('workspace-rail');
    expect(source).toContain('stage-topbar');
  });

  it('hosts the digital human in a global right-side stage', () => {
    expect(source).toContain("import DigitalHumanPanel from '../components/messages/DigitalHumanPanel.vue'");
    expect(source).toContain('workspace-human-stage');
    expect(source).toContain('<DigitalHumanPanel :view-context="digitalHumanContext" />');
    expect(source).toContain("route.name === 'message' ? 'message' : 'default'");
  });

  it('drives primary navigation from the grouped mapping', () => {
    expect(source).toContain('getPrimaryNavigationGroups');
    expect(source).toContain('isNavigationGroupActive');
    expect(source).toContain('visiblePrimaryNavItems');
  });

  it('exposes a lightweight background quick switch in the topbar', () => {
    expect(source).toContain('BackgroundSwitcher');
    expect(source).not.toContain('manualBackgroundUrl');
  });

  it('hides the unused remote audio status from the topbar', () => {
    expect(source).not.toContain('>远程音频</span>');
  });

  it('keeps the desktop rail fixed while only the stage content scrolls', () => {
    expect(layoutCss).toContain('height: 100vh;');
    expect(layoutCss).toContain('.stage-content');
    expect(layoutCss).toContain('overflow-y: auto;');
  });
});
