import { describe, expect, it } from 'vitest';
import { getPrimaryNavigationGroups, isNavigationGroupActive } from './navigationGroups';

describe('navigation groups', () => {
  it('exposes recommendation as a standalone immersive workspace primary entry', () => {
    const groups = getPrimaryNavigationGroups();

    expect(groups.map((item) => item.label)).toEqual(['首页', '对话', '知识', '数字人', '推荐', '数据', '设置']);
    expect(groups).toHaveLength(7);
    expect(groups[0]).toMatchObject({ key: 'home', to: '/', public: true });
  });

  it('keeps existing routes grouped under their immersive primary entry', () => {
    const groups = getPrimaryNavigationGroups();
    const recommendation = groups.find((item) => item.key === 'recommendation');
    const data = groups.find((item) => item.key === 'data');
    const settings = groups.find((item) => item.key === 'settings');

    expect(recommendation?.activePaths).toEqual(expect.arrayContaining(['/app/recommendation', '/app/recommendation/manage']));
    expect(recommendation?.requiresRole).toBeUndefined();
    expect(data?.activePaths).toEqual(expect.arrayContaining(['/app/dashboard', '/app/visitor-report']));
    expect(data?.activePaths).not.toEqual(expect.arrayContaining(['/app/recommendation', '/app/recommendation/manage']));
    expect(settings?.activePaths).toEqual(expect.arrayContaining(['/app/settings', '/app/users']));
  });

  it('marks nested routes active for their primary group', () => {
    const groups = getPrimaryNavigationGroups();
    const recommendation = groups.find((item) => item.key === 'recommendation')!;
    const data = groups.find((item) => item.key === 'data')!;

    expect(isNavigationGroupActive('/app/recommendation/manage', recommendation)).toBe(true);
    expect(isNavigationGroupActive('/app/recommendation/manage', data)).toBe(false);
    expect(isNavigationGroupActive('/app/knowledge', data)).toBe(false);
  });
});
