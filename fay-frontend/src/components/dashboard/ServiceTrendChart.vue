<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue';
import { BarChart, LineChart } from 'echarts/charts';
import {
  AriaComponent,
  GridComponent,
  LegendComponent,
  TooltipComponent,
} from 'echarts/components';
import { init, use, type ECharts, type EChartsCoreOption } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import type { DashboardTrendItem } from '../../api/dashboard';

use([
  AriaComponent,
  BarChart,
  CanvasRenderer,
  GridComponent,
  LegendComponent,
  LineChart,
  TooltipComponent,
]);

const props = defineProps<{ items: DashboardTrendItem[] }>();
const chartElement = ref<HTMLElement | null>(null);
let chart: ECharts | null = null;
let resizeObserver: ResizeObserver | null = null;

function visibleLabelInterval(itemCount: number) {
  const interval = itemCount > 20 ? 4 : itemCount > 10 ? 2 : 1;
  return (index: number) => index % interval === 0 || index === itemCount - 1;
}

function buildAxes(items: DashboardTrendItem[]): EChartsCoreOption {
  return {
    xAxis: {
      type: 'category',
      boundaryGap: true,
      data: items.map((item) => item.date),
      axisLine: { lineStyle: { color: 'rgba(0, 0, 0, 0.12)' } },
      axisTick: { show: false },
      axisLabel: {
        color: '#86868b',
        fontSize: 11,
        hideOverlap: true,
        interval: visibleLabelInterval(items.length),
        formatter: (value: string) => value.slice(5),
      },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { color: '#86868b', fontSize: 11 },
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: 'rgba(0, 0, 0, 0.06)' } },
    },
  };
}

function buildSeries(items: DashboardTrendItem[]) {
  return [
      {
        name: '问答次数',
        type: 'bar',
        data: items.map((item) => item.questions),
        barMaxWidth: 20,
        itemStyle: {
          borderRadius: [6, 6, 0, 0],
          color: '#1687ff',
        },
      },
      {
        name: '服务人次',
        type: 'line',
        data: items.map((item) => item.services),
        smooth: 0.25,
        symbol: 'circle',
        symbolSize: items.length > 20 ? 4 : 6,
        lineStyle: { width: 3, color: '#36b8ff' },
        itemStyle: { color: '#0067e8', borderColor: '#ffffff', borderWidth: 2 },
        areaStyle: { color: 'rgba(54, 184, 255, 0.16)' },
      },
  ];
}

function chartOption(items: DashboardTrendItem[]): EChartsCoreOption {
  const reducedMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  return {
    animation: !reducedMotion,
    aria: { enabled: true },
    color: ['#1687ff', '#36b8ff'],
    grid: { top: 48, right: 18, bottom: 42, left: 44, containLabel: false },
    legend: {
      top: 0,
      right: 4,
      itemWidth: 16,
      itemHeight: 8,
      textStyle: { color: '#4a6b89', fontSize: 12 },
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: '#1687ff', opacity: 0.35 } },
      valueFormatter: (value: number | string) => `${Number(value || 0)} 次`,
    },
    ...buildAxes(items),
    series: buildSeries(items),
  };
}

function renderChart() {
  if (!props.items.length) {
    chart?.clear();
    return;
  }
  if (!chartElement.value) return;
  chart ||= init(chartElement.value);
  chart.setOption(chartOption(props.items), true);
}

onMounted(() => {
  renderChart();
  resizeObserver = new ResizeObserver(() => chart?.resize());
  if (chartElement.value) resizeObserver.observe(chartElement.value);
});

watch(() => props.items, renderChart, { deep: true });

onBeforeUnmount(() => {
  resizeObserver?.disconnect();
  chart?.dispose();
});
</script>

<template>
  <div class="service-trend-frame">
    <div
      ref="chartElement"
      class="service-trend-chart"
      role="img"
      aria-label="服务人次与问答次数趋势图"
    />
    <div v-if="!items.length" class="service-trend-empty">暂无服务趋势数据</div>
  </div>
</template>

<style scoped>
.service-trend-frame {
  position: relative;
  width: 100%;
  height: 278px;
  min-width: 0;
}

.service-trend-chart {
  width: 100%;
  height: 100%;
}

.service-trend-empty {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  color: var(--color-text-secondary);
  font-size: 14px;
}

@media (max-width: 768px) {
  .service-trend-frame {
    height: 230px;
  }
}
</style>
