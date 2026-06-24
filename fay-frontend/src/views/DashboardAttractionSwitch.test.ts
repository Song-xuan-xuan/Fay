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

  it('does not render a dashboard-local digital human after the global stage owns it', () => {
    expect(dashboardSource).not.toContain("import DigitalHumanPanel from '../components/messages/DigitalHumanPanel.vue'");
    expect(dashboardSource).not.toContain('<DigitalHumanPanel');
    expect(dashboardSource).not.toContain('dashboard-right-rail');
    expect(dashboardSource).not.toContain('rightCollapsed');
  });

  it('keeps the dashboard explanation controls available in the dashboard content', () => {
    expect(dashboardSource).toContain('dashboard-insight-panel');
    expect(dashboardSource).toContain("runExplain('overview')");
    expect(dashboardSource).toContain("runExplain('tourism')");
  });
});
