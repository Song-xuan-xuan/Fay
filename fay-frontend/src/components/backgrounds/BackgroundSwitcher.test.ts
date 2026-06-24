import { describe, expect, it } from 'vitest';
import source from './BackgroundSwitcher.vue?raw';

describe('BackgroundSwitcher', () => {
  it('loads uploaded backgrounds and offers manual URL switching', () => {
    expect(source).toContain('loadBackgrounds');
    expect(source).toContain('selectBackground');
    expect(source).toContain('setManualBackground');
    expect(source).toContain('background-quick-switch');
    expect(source).toContain('粘贴背景图片 URL');
  });
});
