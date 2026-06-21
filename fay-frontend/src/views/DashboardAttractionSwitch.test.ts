import { describe, expect, it } from 'vitest';
import dashboardSource from './Dashboard.vue?raw';

describe('Dashboard attraction switch', () => {
  it('scopes tourism dashboard requests to the selected attraction', () => {
    expect(dashboardSource).toContain('灵山胜境');
    expect(dashboardSource).toContain('禅意小镇·拈花湾');
    expect(dashboardSource).toContain('getDashboardOverview(range.value, currentFilters)');
    expect(dashboardSource).toContain('filters: currentTourismFilters()');
    expect(dashboardSource).not.toContain('v-model="filters.attraction_name"');
  });
});
