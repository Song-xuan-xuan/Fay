<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Activity, BarChart3, Database, PanelRightClose, PanelRightOpen, RefreshCw, Sparkles, TrendingUp } from '@lucide/vue';
import {
  explainDashboard,
  getDashboardHotTopics,
  getDashboardOverview,
  getDashboardServiceTrends,
  getDashboardTourism,
  getDashboardUsers,
  reimportDashboardTourism,
  type DashboardOverview,
  type DashboardRange,
  type DashboardTourism,
  type DashboardTrendItem,
  type DashboardUsers,
  type HotTopicItem,
} from '../api/dashboard';
import DigitalHumanPanel from '../components/messages/DigitalHumanPanel.vue';
import VisitorReportPanel from '../components/dashboard/VisitorReportPanel.vue';
import { useAuthStore } from '../stores/auth';

const authStore = useAuthStore();
const range = ref<DashboardRange>('7d');
const activeTab = ref('overview');
const loading = ref(false);
const reimporting = ref(false);
const explaining = ref(false);
const rightCollapsed = ref(false);
const explanation = ref('点击“解读大盘”或“解读景区”，生成当前看板的文本解读。');
const overview = ref<DashboardOverview | null>(null);
const trends = ref<DashboardTrendItem[]>([]);
const topics = ref<HotTopicItem[]>([]);
const tourism = ref<DashboardTourism | null>(null);
const users = ref<DashboardUsers | null>(null);
const filters = reactive({ start_date: '', end_date: '', attraction_type: '', attraction_name: '', satisfaction_min: '', satisfaction_max: '', tourist_segment: '' });
const satisfactionScores = ['1', '2', '3', '4', '5'];
const touristSegments = ['18岁以下', '18-29岁', '30-44岁', '45-59岁', '60岁以上'];

const isAdmin = computed(() => authStore.isAdmin);
const kpis = computed(() => overview.value?.kpis || []);
const maxTrend = computed(() => Math.max(1, ...trends.value.map((item) => Math.max(item.services, item.questions))));
const maxTopic = computed(() => Math.max(1, ...topics.value.map((item) => item.count)));
const maxTypeVisits = computed(() => Math.max(1, ...(tourism.value?.type_metrics || []).map((item) => item.visits)));
const maxCost = computed(() => Math.max(1, ...(tourism.value?.consumption_structure.items || []).map((item) => item.value)));
const maxVisitTrend = computed(() => Math.max(1, ...(tourism.value?.visit_trend || []).map((item) => item.visits)));
const maxSatisfactionDistribution = computed(() => Math.max(1, ...(tourism.value?.satisfaction_distribution || []).map((item) => item.count)));
const maxRegistrationTrend = computed(() => Math.max(1, ...(users.value?.registration_trend || []).map((item) => item.count)));
const maxActiveTrend = computed(() => Math.max(1, ...(users.value?.active_trend || []).map((item) => item.count)));
const trendLinePoints = computed(() => makePolyline(trends.value.map((item) => item.services), 360, 110));
const satisfactionPoints = computed(() => makePolyline((tourism.value?.satisfaction_trend || []).map((item) => item.avg_satisfaction), 240, 80));
const sourceRecordCount = computed(() => tourism.value?.source.record_count || tourism.value?.source.row_count || 0);

async function loadDashboard() {
  loading.value = true;
  try {
    const [overviewData, trendData, topicData, tourismData, userData] = await Promise.all([
      getDashboardOverview(range.value),
      getDashboardServiceTrends(range.value),
      getDashboardHotTopics(range.value),
      getDashboardTourism(filters),
      getDashboardUsers(),
    ]);
    overview.value = overviewData;
    trends.value = trendData.items || [];
    topics.value = topicData.items || [];
    tourism.value = tourismData;
    users.value = userData;
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载看板失败');
  } finally {
    loading.value = false;
  }
}

async function loadTourism() {
  try {
    tourism.value = await getDashboardTourism(filters);
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载旅游分析失败');
  }
}

async function handleRangeChange() {
  await loadDashboard();
}

async function handleReimport() {
  try {
    await ElMessageBox.confirm('将重新读取 data 目录 Excel 并重建 tourism.db，确认继续？', '重新导入', { type: 'warning' });
  } catch {
    return;
  }
  reimporting.value = true;
  try {
    await reimportDashboardTourism();
    ElMessage.success('旅游 Excel 已重新导入');
    await loadDashboard();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '重新导入失败');
  } finally {
    reimporting.value = false;
  }
}

async function runExplain(scope: string) {
  explaining.value = true;
  try {
    const result = await explainDashboard({ scope, range: range.value, overview: overview.value, topics: topics.value.slice(0, 5), tourism: tourism.value?.source });
    explanation.value = result.text || '暂无解读结果';
    rightCollapsed.value = false;
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '生成解读失败');
  } finally {
    explaining.value = false;
  }
}

function percent(value: number, max: number) {
  return `${Math.max(2, Math.round((Number(value || 0) / max) * 100))}%`;
}

function formatTime(timestamp?: number) {
  if (!timestamp) return '-';
  return new Date(timestamp * 1000).toLocaleString();
}

function makePolyline(values: number[], width: number, height: number) {
  if (!values.length) return '';
  const max = Math.max(1, ...values);
  const step = values.length > 1 ? width / (values.length - 1) : width;
  return values.map((value, index) => `${index * step},${height - (value / max) * (height - 8) - 4}`).join(' ');
}

onMounted(loadDashboard);
</script>

<template>
  <section class="dashboard-shell" :class="{ 'right-collapsed': rightCollapsed }" v-loading="loading">
    <div class="dashboard-main">
      <div class="dashboard-title-row">
        <div>
          <h2>数字人服务运营大屏</h2>
          <p>汇总数字人服务、用户增长、热门问答与景区旅游行为数据</p>
        </div>
        <div class="dashboard-actions">
          <el-select v-model="range" class="range-select" @change="handleRangeChange">
            <el-option label="最近 7 天" value="7d" />
            <el-option label="最近 30 天" value="30d" />
            <el-option label="本周" value="week" />
            <el-option label="本月" value="month" />
          </el-select>
          <el-button :icon="RefreshCw" :loading="loading" @click="loadDashboard">刷新</el-button>
          <el-button v-if="isAdmin" :icon="Database" :loading="reimporting" @click="handleReimport">重新导入</el-button>
        </div>
      </div>

      <div class="data-source-strip">
        <span>服务运营数据：系统运行数据</span>
        <span>用户数据：用户管理模块</span>
        <span>旅游行为数据：Excel 导入 SQLite</span>
        <el-tag v-if="overview?.is_demo" type="warning">演示数据</el-tag>
      </div>

      <div class="kpi-grid">
        <article v-for="item in kpis" :key="item.title" class="kpi-card">
          <span class="kpi-source">{{ item.source }}</span>
          <strong>{{ item.value }}<small>{{ item.unit }}</small></strong>
          <p>{{ item.title }}</p>
        </article>
      </div>

      <div class="hero-charts">
        <section class="chart-panel trend-panel">
          <div class="section-head"><TrendingUp :size="18" /><h3>近 {{ range === '30d' ? 30 : 7 }} 日服务趋势</h3></div>
          <div class="trend-chart">
            <div v-for="item in trends" :key="item.date" class="trend-column">
              <span class="bar questions" :style="{ height: percent(item.questions, maxTrend) }" />
              <span class="bar services" :style="{ height: percent(item.services, maxTrend) }" />
              <small>{{ item.date.slice(5) }}</small>
            </div>
            <svg viewBox="0 0 360 110" preserveAspectRatio="none" aria-hidden="true"><polyline :points="trendLinePoints" /></svg>
          </div>
        </section>

        <section class="chart-panel compact-panel">
          <div class="section-head"><BarChart3 :size="18" /><h3>热门问答 TOP5</h3></div>
          <div class="rank-list">
            <div v-for="topic in topics.slice(0, 5)" :key="topic.topic" class="rank-row">
              <span>{{ topic.topic }}</span><b>{{ topic.count }}</b>
              <i :style="{ width: percent(topic.count, maxTopic) }" />
            </div>
          </div>
        </section>

        <section class="chart-panel compact-panel">
          <div class="section-head"><Activity :size="18" /><h3>游客满意度趋势</h3></div>
          <svg class="mini-line" viewBox="0 0 240 80" preserveAspectRatio="none" aria-label="满意度趋势"><polyline :points="satisfactionPoints" /></svg>
          <p class="panel-note">平均 {{ tourism?.average_satisfaction?.toFixed(2) || '0.00' }} 分，低满意 {{ tourism?.low_satisfaction_count || 0 }} 条</p>
        </section>
      </div>

      <el-tabs v-model="activeTab" class="dashboard-tabs">
        <el-tab-pane label="运营概览" name="overview">
          <div class="split-grid">
            <section class="chart-panel"><h3>服务趋势明细</h3><el-table :data="trends" height="320"><el-table-column prop="date" label="日期" /><el-table-column prop="services" label="服务人次" /><el-table-column prop="questions" label="问答次数" /><el-table-column prop="active_users" label="活跃用户" /></el-table></section>
            <section class="chart-panel"><h3>数据来源</h3><p class="source-text">旅游记录 {{ sourceRecordCount }} 条，时间范围 {{ tourism?.source.date_range?.start || '-' }} 至 {{ tourism?.source.date_range?.end || '-' }}，最后导入 {{ formatTime(tourism?.source.imported_at) }}。</p></section>
          </div>
        </el-tab-pane>
        <el-tab-pane label="用户活跃" name="users">
          <div class="split-grid"><section class="chart-panel"><h3>注册趋势</h3><div class="rank-list"><div v-for="item in users?.registration_trend || []" :key="`registration-${item.date}`" class="rank-row"><span>{{ item.date }}</span><b>{{ item.count }}</b><i :style="{ width: percent(item.count, maxRegistrationTrend) }" /></div></div></section><section class="chart-panel"><h3>活跃趋势</h3><div class="rank-list"><div v-for="item in users?.active_trend || []" :key="`active-${item.date}`" class="rank-row"><span>{{ item.date }}</span><b>{{ item.count }}</b><i :style="{ width: percent(item.count, maxActiveTrend) }" /></div></div></section></div>
          <div class="split-grid user-detail-grid"><section class="chart-panel"><h3>角色分布</h3><div class="rank-list"><div v-for="role in users?.role_distribution || []" :key="role.role" class="rank-row"><span>{{ role.role }}</span><b>{{ role.count }}</b><i :style="{ width: percent(role.count, users?.total_users || 1) }" /></div></div></section><section class="chart-panel"><h3>最近活跃用户</h3><el-table :data="users?.recent_users || []" height="320"><el-table-column prop="username" label="用户" /><el-table-column prop="role" label="角色" width="100" /><el-table-column prop="email" label="邮箱" /><el-table-column label="最后登录" width="170"><template #default="{ row }">{{ formatTime(row.last_login) }}</template></el-table-column></el-table></section></div>
        </el-tab-pane>
        <el-tab-pane label="热门问答" name="topics">
          <section class="chart-panel"><h3>主题聚合</h3><div class="topic-grid"><article v-for="topic in topics" :key="topic.topic" class="topic-item"><strong>{{ topic.topic }}</strong><span>{{ topic.count }} 次 · {{ Math.round(topic.ratio * 100) }}%</span><p>{{ topic.representative_question || '暂无代表问题' }}</p></article></div></section>
        </el-tab-pane>
        <el-tab-pane v-if="isAdmin" label="游客感受度" name="visitor-report">
          <VisitorReportPanel />
        </el-tab-pane>
        <el-tab-pane label="景区分析" name="tourism">
          <section class="filter-row"><el-date-picker v-model="filters.start_date" value-format="YYYY-MM-DD" placeholder="开始日期" /><el-date-picker v-model="filters.end_date" value-format="YYYY-MM-DD" placeholder="结束日期" /><el-input v-model="filters.attraction_type" placeholder="景区类型" /><el-input v-model="filters.attraction_name" placeholder="景点名称" /><el-select v-model="filters.satisfaction_min" clearable placeholder="最低满意度"><el-option v-for="score in satisfactionScores" :key="`min-${score}`" :label="score" :value="score" /></el-select><el-select v-model="filters.satisfaction_max" clearable placeholder="最高满意度"><el-option v-for="score in satisfactionScores" :key="`max-${score}`" :label="score" :value="score" /></el-select><el-select v-model="filters.tourist_segment" clearable placeholder="游客分群"><el-option v-for="segment in touristSegments" :key="segment" :label="segment" :value="segment" /></el-select><el-button type="primary" @click="loadTourism">筛选</el-button></section>
          <div class="split-grid"><section class="chart-panel"><h3>景区类型访问量</h3><div class="rank-list"><div v-for="item in tourism?.type_metrics || []" :key="item.name" class="rank-row"><span>{{ item.name }}</span><b>{{ item.visits }}</b><i :style="{ width: percent(item.visits, maxTypeVisits) }" /></div></div></section><section class="chart-panel"><h3>景点 TOP10</h3><el-table :data="tourism?.attraction_ranking || []" height="360"><el-table-column prop="attraction_name" label="景点" min-width="160" /><el-table-column prop="attraction_type" label="类型" width="120" /><el-table-column prop="visits" label="访问" width="90" /><el-table-column prop="avg_satisfaction" label="满意度" width="100" /></el-table></section></div>
          <div class="split-grid tourism-trend-grid"><section class="chart-panel"><h3>游客访问趋势</h3><div class="rank-list"><div v-for="item in tourism?.visit_trend || []" :key="item.month" class="rank-row"><span>{{ item.month }} · {{ item.tourists }} 人</span><b>{{ item.visits }}</b><i :style="{ width: percent(item.visits, maxVisitTrend) }" /></div></div></section><section class="chart-panel"><h3>满意度分布</h3><div class="rank-list"><div v-for="item in tourism?.satisfaction_distribution || []" :key="item.name" class="rank-row"><span>{{ item.name }}</span><b>{{ item.count }}</b><i :style="{ width: percent(item.count, maxSatisfactionDistribution) }" /></div></div></section></div>
        </el-tab-pane>
        <el-tab-pane label="游客画像" name="profile">
          <div class="split-grid"><section class="chart-panel"><h3>人均消费结构</h3><div class="rank-list"><div v-for="item in tourism?.consumption_structure.items || []" :key="item.name" class="rank-row"><span>{{ item.name }}</span><b>{{ item.value }}</b><i :style="{ width: percent(item.value, maxCost) }" /></div></div></section><section class="chart-panel"><h3>游客分群</h3><div class="topic-grid"><article v-for="item in tourism?.tourist_profile.age_groups || []" :key="item.name" class="topic-item"><strong>{{ item.name }}</strong><span>{{ item.count }} 人次</span></article></div></section></div>
        </el-tab-pane>
        <el-tab-pane label="明细数据" name="details">
          <section class="chart-panel"><h3>景区访问明细</h3><el-table :data="tourism?.details || []" height="430"><el-table-column prop="visit_date" label="日期" width="120" /><el-table-column prop="tourist_id" label="游客" width="110" /><el-table-column prop="attraction_name" label="景点" min-width="200" /><el-table-column prop="attraction_type" label="类型" width="120" /><el-table-column prop="tourist_segment" label="分群" width="110" /><el-table-column prop="total_cost" label="消费" width="100" /><el-table-column prop="satisfaction" label="满意度" width="90" /></el-table></section>
        </el-tab-pane>
      </el-tabs>
    </div>

    <aside class="dashboard-right-rail" :class="{ collapsed: rightCollapsed }">
      <DigitalHumanPanel v-if="!rightCollapsed" />
      <section class="dashboard-insight" :class="{ collapsed: rightCollapsed }">
        <button class="collapse-button" type="button" @click="rightCollapsed = !rightCollapsed" :aria-label="rightCollapsed ? '展开看板解读' : '折叠看板解读'">
          <PanelRightOpen v-if="rightCollapsed" :size="18" /><PanelRightClose v-else :size="18" />
        </button>
        <template v-if="!rightCollapsed">
          <div class="insight-avatar"><Sparkles :size="22" /></div>
          <h3>看板智能解读</h3>
          <p class="panel-note">右侧数字人负责呈现，文本解读可辅助复盘看板数据。</p>
          <div class="insight-actions"><el-button size="small" :loading="explaining" @click="runExplain('overview')">解读大盘</el-button><el-button size="small" @click="runExplain('tourism')">解读景区</el-button></div>
          <div class="insight-text">{{ explanation }}</div>
        </template>
      </section>
    </aside>
  </section>
</template>
