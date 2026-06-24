import { describe, expect, it } from 'vitest';
import { getPrimaryNavigationGroups, isNavigationGroupActive } from './navigationGroups';

describe('navigation groups', () => {
  it('exposes recommendation as a standalone immersive workspace primary entry', () => {
    const groups = getPrimaryNavigationGroups();

    expect(groups.map((item) => item.label)).toEqual(['对话', '知识', '数字人', '推荐', '数据', '设置']);
    expect(groups).toHaveLength(6);
  });

  it('keeps existing routes grouped under their immersive primary entry', () => {
    const groups = getPrimaryNavigationGroups();
    const recommendation = groups.find((item) => item.key === 'recommendation');
    const data = groups.find((item) => item.key === 'data');
    const settings = groups.find((item) => item.key === 'settings');

    expect(recommendation?.activePaths).toEqual(expect.arrayContaining(['/recommendation', '/recommendation/manage']));
    expect(recommendation?.requiresRole).toBeUndefined();
    expect(data?.activePaths).toEqual(expect.arrayContaining(['/dashboard', '/visitor-report']));
    expect(data?.activePaths).not.toEqual(expect.arrayContaining(['/recommendation', '/recommendation/manage']));
    expect(settings?.activePaths).toEqual(expect.arrayContaining(['/mcp', '/users', '/setting']));
  });

  it('marks nested routes active for their primary group', () => {
    const groups = getPrimaryNavigationGroups();
    const recommendation = groups.find((item) => item.key === 'recommendation')!;
    const data = groups.find((item) => item.key === 'data')!;

    expect(isNavigationGroupActive('/recommendation/manage', recommendation)).toBe(true);
    expect(isNavigationGroupActive('/recommendation/manage', data)).toBe(false);
    expect(isNavigationGroupActive('/knowledge', data)).toBe(false);
  });
});
