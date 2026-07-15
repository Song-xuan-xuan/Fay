import { describe, expect, it } from 'vitest';
import { getTourismPeriodRange, tourismPeriodOptions } from './dashboardPeriods';

describe('dashboard tourism periods', () => {
  it('maps all data and quarter filters to independent tourism dates', () => {
    expect(getTourismPeriodRange('all')).toEqual({ startDate: '', endDate: '' });
    expect(getTourismPeriodRange('2025-q1')).toEqual({
      startDate: '2025-01-01',
      endDate: '2025-03-31',
    });
  });

  it('provides every month in the 2025 tourism dataset', () => {
    expect(tourismPeriodOptions).toHaveLength(17);
    expect(getTourismPeriodRange('2025-02')).toEqual({
      startDate: '2025-02-01',
      endDate: '2025-02-28',
    });
  });
});
