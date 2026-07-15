import { describe, expect, it } from 'vitest';
import contentSource from './homeContent.ts?raw';
import { HOME_SECTIONS, HOME_ROUTES, HOME_INSIGHTS } from './homeContent';

describe('public homepage content', () => {
  it('keeps all seven cinematic sections', () => {
    expect(HOME_SECTIONS).toHaveLength(7);
    expect(HOME_SECTIONS.map((item) => item.id)).toEqual([
      'hero', 'guide', 'rag', 'route', 'network', 'insights', 'cta',
    ]);
  });

  it('preserves the complete six-hour historic route from the source material', () => {
    expect(HOME_ROUTES[0].duration).toBe('6 小时');
    expect(HOME_ROUTES[0].stops).toEqual([
      '南门入园', '灵山大照壁（华夏第一壁）', '胜境广场', '佛手广场（天下第一掌）',
      '祥符禅寺', '杏坛广场', '佛前广场', '灵山大佛', '灵山梵宫',
      '五印坛城', '三圣殿', '出口',
    ]);
  });

  it('keeps the fixed real insight values without exposing source-path metadata', () => {
    expect(HOME_INSIGHTS.map((item) => item.value)).toEqual(['3.99', '2.71', '3.04', '236']);
    expect(contentSource).not.toContain('HOME_SOURCES');
    expect(contentSource).not.toContain('sample: 236');
  });
});
