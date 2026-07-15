import { existsSync, readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';

function readSource(relativePath: string) {
  const path = fileURLToPath(new URL(relativePath, import.meta.url));
  return existsSync(path) ? readFileSync(path, 'utf8') : '';
}

const dashboardSource = readSource('./Dashboard.vue');
const kpiGridSource = readSource('../components/dashboard/DashboardKpiGrid.vue');
const attractionComparisonSource = readSource('../components/dashboard/AttractionComparison.vue');
const serviceTrendSource = readSource('../components/dashboard/ServiceTrendChart.vue');
const visualStyles = readSource('../styles/dashboard-visual.css');
const responsiveStyles = readSource('../styles/dashboard-visual-responsive.css');
const railStyles = readSource('../styles/dashboard-rail.css');

void attractionComparisonSource;
void serviceTrendSource;
void visualStyles;
void responsiveStyles;
void railStyles;

describe('Dashboard visual refresh', () => {
  it('integrates the reusable KPI grid for global and tourism metrics', () => {
    expect(dashboardSource).toContain("import DashboardKpiGrid from '../components/dashboard/DashboardKpiGrid.vue'");
    expect(dashboardSource).toContain('<DashboardKpiGrid :items="kpis" variant="global" />');
    expect(dashboardSource).toContain('<DashboardKpiGrid :tourism="tourism" :source="selectedAttraction" variant="tourism" />');
    expect(kpiGridSource).toContain('dashboard-kpi-grid');
    expect(kpiGridSource).toContain('kpi-card--global');
    expect(kpiGridSource).toContain('kpi-card--tourism');
  });

  it('keeps the selected attraction visible in the comparison table', () => {
    expect(dashboardSource).toContain(':selected-attraction="selectedAttraction"');
    expect(attractionComparisonSource).toContain(':row-class-name="rowClassName"');
    expect(attractionComparisonSource).toContain('is-selected-attraction');
  });

  it('uses a blue and cyan chart treatment with an area fill', () => {
    expect(serviceTrendSource).toContain('function buildSeries');
    expect(serviceTrendSource).toContain('areaStyle');
    expect(serviceTrendSource).toContain('#1687ff');
  });

  it('scopes the dashboard visual system and responsive motion rules', () => {
    expect(visualStyles).toContain('.dashboard-shell .dashboard-kpi-grid');
    expect(visualStyles).toContain('is-selected-attraction');
    expect(railStyles).toContain('.dashboard-shell .dashboard-insight-panel');
    expect(railStyles).not.toMatch(/^\.insight-/m);
    expect(railStyles).not.toContain('letter-spacing: -');
    expect(responsiveStyles).toContain('grid-template-columns: repeat(4, minmax(0, 1fr))');
    expect(responsiveStyles).toContain('grid-template-columns: repeat(2, minmax(0, 1fr))');
    expect(responsiveStyles).toContain('@media (prefers-reduced-motion: reduce)');
  });

  it('keeps the dashboard header clean and gives global KPIs distinct icons', () => {
    expect(visualStyles).toContain('.dashboard-shell .data-source-strip:empty');
    expect(visualStyles).toContain('.dashboard-title-row > div:first-child');
    expect(kpiGridSource).toContain('今日问答次数: MessageCircle');
    expect(kpiGridSource).toContain('今日新增注册: UserPlus');
    expect(kpiGridSource).toContain('kpi-card--contextual');
  });

  it('centers attraction switch labels inside their fixed-height buttons', () => {
    expect(visualStyles).toMatch(/\.dashboard-shell \.attraction-switch \.el-radio-button__inner \{[^}]*display: inline-flex;[^}]*align-items: center;[^}]*justify-content: center;/s);
  });
});
