import { describe, expect, it } from 'vitest';

describe('buildTourismKpis', () => {
  it('formats tourism KPI values and keeps the attraction source', async () => {
    const { buildTourismKpis } = await import('./dashboardKpis');
    const items = buildTourismKpis({
      visit_count: 12,
      tourist_count: 8,
      average_satisfaction: 4.56,
      low_satisfaction_rate: 0.125,
      average_total_cost: 88.6,
      average_stay_duration: 3.25,
    }, '灵山胜境');

    expect(items.map((item) => item.value)).toEqual([12, 8, '4.56', 12.5, '88.60', '3.25']);
    expect(items.every((item) => item.source === '灵山胜境')).toBe(true);
  });

  it('returns stable empty values for null tourism data', async () => {
    const { buildTourismKpis } = await import('./dashboardKpis');
    const items = buildTourismKpis(null, '灵山胜境');

    expect(items.map((item) => item.value)).toEqual([0, 0, '0.00', 0, '0.00', '0.00']);
  });
});
