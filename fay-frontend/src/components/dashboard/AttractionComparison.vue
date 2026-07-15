<script setup lang="ts">
import { computed } from 'vue';
import type { DashboardTourism } from '../../api/dashboard';

export interface AttractionComparisonItem {
  name: string;
  data: DashboardTourism;
}

const props = defineProps<{
  items: AttractionComparisonItem[];
  selectedAttraction?: string;
}>();

const rows = computed(() => props.items.map(({ name, data }) => ({
  name,
  visits: data.visit_count,
  tourists: data.tourist_count,
  satisfaction: data.average_satisfaction,
  lowRate: `${Math.round(data.low_satisfaction_rate * 1000) / 10}%`,
  averageCost: data.average_total_cost,
  averageStay: data.average_stay_duration,
})));

function rowClassName({ row }: { row: { name: string } }) {
  return row.name === props.selectedAttraction ? 'is-selected-attraction' : '';
}
</script>

<template>
  <section class="chart-panel attraction-comparison">
    <h3>双景区关键指标对比</h3>
    <el-table :data="rows" :row-class-name="rowClassName" empty-text="暂无景区对比数据">
      <el-table-column prop="name" label="景区" min-width="170" />
      <el-table-column prop="visits" label="访问人次" min-width="100" />
      <el-table-column prop="tourists" label="独立游客" min-width="100" />
      <el-table-column prop="satisfaction" label="平均满意度" min-width="110" />
      <el-table-column prop="lowRate" label="低满意率" min-width="100" />
      <el-table-column prop="averageCost" label="人均消费（元）" min-width="120" />
      <el-table-column prop="averageStay" label="平均停留（小时）" min-width="140" />
    </el-table>
  </section>
</template>

<style scoped>
.attraction-comparison {
  margin-top: 16px;
}
</style>
