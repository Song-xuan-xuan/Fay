import { describe, expect, it } from 'vitest';
import source from './Live2D.vue?raw';

describe('Live2D view', () => {
  it('keeps Live2D renderers out of the card grid to avoid many WebGL instances', () => {
    expect(source).toContain('v-if="hasCustomCover(human)"');
    expect(source).not.toContain('class="human-cover-frame"');
    expect(source).not.toContain(':src="human.render_url"');
  });

  it('shows a model-specific placeholder when a card only has the default cover', () => {
    expect(source).toContain('function hasCustomCover');
    expect(source).toContain('function modelInitials');
    expect(source).toContain('function coverAccentStyle');
    expect(source).toContain('class="human-cover-placeholder"');
    expect(source).toContain(':style="coverAccentStyle(human)"');
    expect(source).toContain('{{ modelInitials(human) }}');
  });

  it('loads one renderer only inside the preview dialog and destroys it on close', () => {
    expect(source).toContain('const previewRenderUrl = computed');
    expect(source).toMatch(/<el-dialog[\s\S]*destroy-on-close[\s\S]*@closed="clearPreview"/);
    expect(source).toMatch(/<iframe[\s\S]*v-if="previewRenderUrl"[\s\S]*:src="previewRenderUrl"/);
  });

  it('opens global interaction settings from the digital human library toolbar', () => {
    expect(source).toContain('InteractionSettingsDrawer');
    expect(source).toContain('交互设置');
    expect(source).toContain('settingsVisible');
  });
});
