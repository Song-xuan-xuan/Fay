import { describe, expect, it } from 'vitest';
import source from './InteractionSettingsDrawer.vue?raw';

describe('InteractionSettingsDrawer', () => {
  it('keeps global interaction settings out of the primary sidebar persona page', () => {
    expect(source).toContain('交互设置');
    expect(source).toContain('Q&A 文件');
    expect(source).toContain('唤醒词');
    expect(source).toContain('服务器麦克风');
    expect(source).toContain('自动播报');

    expect(source).not.toContain('label="姓名"');
    expect(source).not.toContain('label="性别"');
    expect(source).not.toContain('label="出生地"');
    expect(source).not.toContain('label="声音选择"');
  });
});
