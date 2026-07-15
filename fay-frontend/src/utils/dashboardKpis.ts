export interface DashboardKpiItem {
  title: string;
  value: number | string;
  unit: string;
  source: string;
}

export interface TourismKpiSource {
  visit_count?: number | null;
  tourist_count?: number | null;
  average_satisfaction?: number | null;
  low_satisfaction_rate?: number | null;
  average_total_cost?: number | null;
  average_stay_duration?: number | null;
}

export function buildTourismKpis(
  tourism: TourismKpiSource | null | undefined,
  source: string,
): DashboardKpiItem[] {
  return [
    { title: '景区访问人次', value: tourism?.visit_count ?? 0, unit: '人次', source },
    { title: '独立游客', value: tourism?.tourist_count ?? 0, unit: '人', source },
    { title: '平均满意度', value: (tourism?.average_satisfaction ?? 0).toFixed(2), unit: '分', source },
    { title: '低满意率', value: Math.round((tourism?.low_satisfaction_rate ?? 0) * 1000) / 10, unit: '%', source },
    { title: '人均消费', value: (tourism?.average_total_cost ?? 0).toFixed(2), unit: '元', source },
    { title: '平均停留时长', value: (tourism?.average_stay_duration ?? 0).toFixed(2), unit: '小时', source },
  ];
}
