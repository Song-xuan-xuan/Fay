import { describe, expect, it } from 'vitest';
import source from './BackgroundManager.vue?raw';

describe('BackgroundManager', () => {
  it('supports uploaded background management in the settings group', () => {
    expect(source).toContain('uploadBackground');
    expect(source).toContain('activateBackground');
    expect(source).toContain('deleteBackground');
    expect(source).toContain('selectBackground');
    expect(source).toContain('background-manager');
    expect(source).toContain('设为全局');
  });
});
