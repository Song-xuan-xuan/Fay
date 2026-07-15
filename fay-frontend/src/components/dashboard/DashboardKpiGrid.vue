<script setup lang="ts">
import { computed, type Component } from 'vue';
import {
  Activity,
  AlertTriangle,
  Clock,
  MessageCircle,
  Star,
  UserPlus,
  Users,
  Wallet,
} from '@lucide/vue';
import {
  buildTourismKpis,
  type DashboardKpiItem,
  type TourismKpiSource,
} from '../../utils/dashboardKpis';

const props = withDefaults(defineProps<{
  items?: DashboardKpiItem[];
  variant?: 'global' | 'tourism';
  tourism?: TourismKpiSource | null;
  source?: string;
}>(), {
  items: () => [],
  variant: 'global',
  tourism: null,
  source: '',
});

const iconsByTitle: Record<string, Component> = {
  今日服务人次: Activity,
  本周服务人次: Activity,
  今日问答次数: MessageCircle,
  今日新增注册: UserPlus,
  累计注册用户: Users,
  本周活跃用户: Users,
  游客平均满意度: Star,
  低满意预警: AlertTriangle,
  景区访问人次: Activity,
  独立游客: Users,
  平均满意度: Star,
  低满意率: AlertTriangle,
  人均消费: Wallet,
  平均停留时长: Clock,
};

const displayItems = computed(() => props.variant === 'tourism'
  ? buildTourismKpis(props.tourism, props.source)
  : props.items);

function iconFor(title: string) {
  return iconsByTitle[title] || Activity;
}

function isAttractionMetric(item: DashboardKpiItem) {
  return props.variant === 'global' && item.source.includes('当前景区');
}
</script>

<template>
  <div
    class="kpi-grid dashboard-kpi-grid"
    :class="{ 'tourism-kpi-grid': variant === 'tourism' }"
    role="list"
  >
    <article
      v-for="item in displayItems"
      :key="item.title"
      class="kpi-card"
      :class="{
        'kpi-card--global': variant === 'global' && !isAttractionMetric(item),
        'kpi-card--contextual': isAttractionMetric(item),
        'kpi-card--tourism': variant === 'tourism',
      }"
      role="listitem"
    >
      <span class="kpi-icon" aria-hidden="true">
        <component :is="iconFor(item.title)" :size="20" />
      </span>
      <span class="kpi-source">{{ item.source }}</span>
      <strong class="kpi-value">{{ item.value }}<small>{{ item.unit }}</small></strong>
      <p class="kpi-title">{{ item.title }}</p>
    </article>
  </div>
</template>
