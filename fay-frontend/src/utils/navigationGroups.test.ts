import { describe, expect, it } from 'vitest';
import { getPrimaryNavigationGroups, isNavigationGroupActive } from './navigationGroups';

describe('navigation groups', () => {
  it('exposes the five immersive workspace primary entries', () => {
    const groups = getPrimaryNavigationGroups();

    expect(groups.map((item) => item.label)).toEqual(['对话', '知识', '数字人', '数据', '设置']);
    expect(groups).toHaveLength(5);
  });

  it('keeps existing routes grouped under their immersive primary entry', () => {
    const groups = getPrimaryNavigationGroups();
    const data = groups.find((item) => item.key === 'data');
    const settings = groups.find((item) => item.key === 'settings');

    expect(data?.activePaths).toEqual(expect.arrayContaining(['/dashboard', '/visitor-report', '/recommendation', '/recommendation/manage']));
    expect(settings?.activePaths).toEqual(expect.arrayContaining(['/mcp', '/users', '/setting']));
  });

  it('marks nested routes active for their primary group', () => {
    const groups = getPrimaryNavigationGroups();
    const data = groups.find((item) => item.key === 'data')!;

    expect(isNavigationGroupActive('/recommendation/manage', data)).toBe(true);
    expect(isNavigationGroupActive('/knowledge', data)).toBe(false);
  });
});
