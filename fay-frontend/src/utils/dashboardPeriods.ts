const TOURISM_DATA_YEAR = 2025;

export interface TourismPeriodOption {
  label: string;
  value: string;
  startDate: string;
  endDate: string;
}

function pad(value: number) {
  return String(value).padStart(2, '0');
}

function monthEnd(year: number, month: number) {
  return new Date(Date.UTC(year, month, 0)).getUTCDate();
}

function quarterOptions(year: number): TourismPeriodOption[] {
  return Array.from({ length: 4 }, (_, index) => {
    const startMonth = index * 3 + 1;
    const endMonth = startMonth + 2;
    return {
      label: `${year} 年第 ${index + 1} 季度`,
      value: `${year}-q${index + 1}`,
      startDate: `${year}-${pad(startMonth)}-01`,
      endDate: `${year}-${pad(endMonth)}-${monthEnd(year, endMonth)}`,
    };
  });
}

function monthOptions(year: number): TourismPeriodOption[] {
  return Array.from({ length: 12 }, (_, index) => {
    const month = index + 1;
    return {
      label: `${year} 年 ${month} 月`,
      value: `${year}-${pad(month)}`,
      startDate: `${year}-${pad(month)}-01`,
      endDate: `${year}-${pad(month)}-${monthEnd(year, month)}`,
    };
  });
}

export const tourismPeriodOptions: TourismPeriodOption[] = [
  { label: '全部旅游数据', value: 'all', startDate: '', endDate: '' },
  ...quarterOptions(TOURISM_DATA_YEAR),
  ...monthOptions(TOURISM_DATA_YEAR),
];

export function getTourismPeriodRange(value: string) {
  const option = tourismPeriodOptions.find((item) => item.value === value);
  return { startDate: option?.startDate || '', endDate: option?.endDate || '' };
}
