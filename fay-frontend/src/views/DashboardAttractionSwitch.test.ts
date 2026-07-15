import { describe, expect, it } from 'vitest';
import serviceTrendSource from '../components/dashboard/ServiceTrendChart.vue?raw';
import dashboardSource from './Dashboard.vue?raw';

describe('Dashboard attraction switch', () => {
  it('scopes tourism dashboard requests to the selected attraction', () => {
    expect(dashboardSource).toContain('灵山胜境');
    expect(dashboardSource).toContain('禅意小镇·拈花湾');
    expect(dashboardSource).toContain('getDashboardOverview(range.value, currentFilters)');
    expect(dashboardSource).toContain('filters: currentTourismFilters()');
    expect(dashboardSource).not.toContain('v-model="filters.attraction_name"');
    expect(dashboardSource).toContain(':value="name"');
    expect(dashboardSource).not.toContain(':label="name"');
    expect(dashboardSource).toContain('{{ name }}');
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

  it('uses a responsive chart component for long service ranges', () => {
    expect(dashboardSource).toContain("import ServiceTrendChart from '../components/dashboard/ServiceTrendChart.vue'");
    expect(dashboardSource).toContain('<ServiceTrendChart :items="trends" />');
    expect(dashboardSource).not.toContain('class="trend-chart"');
    expect(dashboardSource).not.toContain('trendLinePoints');
  });

  it('keeps the chart element stable while trend data is temporarily empty', () => {
    expect(serviceTrendSource).toContain('class="service-trend-frame"');
    expect(serviceTrendSource).toContain('chart?.clear()');
  });

  it('separates tourism periods and connects attraction-specific KPIs', () => {
    expect(dashboardSource).toContain('class="tourism-period-select"');
    expect(dashboardSource).toContain("import DashboardKpiGrid from '../components/dashboard/DashboardKpiGrid.vue'");
    expect(dashboardSource).toContain('<DashboardKpiGrid :tourism="tourism" :source="selectedAttraction" variant="tourism" />');
    expect(dashboardSource).not.toContain('v-model="filters.attraction_type"');
    expect(dashboardSource).not.toContain('景点 TOP10');
  });

  it('loads both attractions for a side-by-side comparison', () => {
    expect(dashboardSource).toContain('loadAttractionComparison');
    expect(dashboardSource).toContain('<AttractionComparison :items="attractionComparison" :selected-attraction="selectedAttraction" />');
  });
});
