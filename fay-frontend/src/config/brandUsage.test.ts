import { describe, expect, it } from 'vitest';
import appLayoutSource from '../layouts/AppLayout.vue?raw';
import loginSource from '../views/Login.vue?raw';
import sharePreviewSource from '../components/messages/SharePreviewDialog.vue?raw';
import settingSource from '../views/Setting.vue?raw';
import interactionSettingsSource from '../components/digital-humans/InteractionSettingsDrawer.vue?raw';
import chatComposerSource from '../components/messages/ChatComposer.vue?raw';
import messageSubmitSource from '../composables/useMessageSubmit.ts?raw';
import audioActionsSource from '../composables/useAudioControlActions.ts?raw';
import mainSource from '../main.ts?raw';
import viteConfigSource from '../../vite.config.ts?raw';
import indexHtmlSource from '../../index.html?raw';

const visibleBrandSources = [
  appLayoutSource,
  loginSource,
  sharePreviewSource,
  settingSource,
  interactionSettingsSource,
  chatComposerSource,
  messageSubmitSource,
  audioActionsSource,
];

describe('visible brand usage', () => {
  it('does not leave legacy Fay copy in visible Vue surfaces', () => {
    for (const source of visibleBrandSources) {
      expect(source).not.toContain('Fay Console');
      expect(source).not.toContain('Fay 开源数字人');
      expect(source).not.toContain('Fay 服务');
      expect(source).not.toContain('Fay 的');
      expect(source).not.toContain('启动 Fay');
      expect(source).not.toContain('请先开启 Fay');
      expect(source).not.toContain('alt="Fay"');
    }
  });

  it('uses the brand config for runtime and HTML title branding', () => {
    expect(mainSource).toContain('applyBrandDocumentTitle');
    expect(viteConfigSource).toContain('BRAND_CONSOLE_NAME');
    expect(indexHtmlSource).toContain('%BRAND_CONSOLE_NAME%');
  });
});
