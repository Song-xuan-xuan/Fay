<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { RouterLink, useRoute } from 'vue-router';
import { ElMessage } from 'element-plus';
import { Clipboard, Download, History, Printer, RefreshCw, Route, Save, Settings, Sparkles, ThumbsDown, ThumbsUp, Trees, Users } from '@lucide/vue';
import {
  createRecommendation,
  deleteRecommendationPreferences,
  getRecommendationPreferences,
  listRecommendationHistory,
  saveRecommendationPreferences,
  submitRecommendationFeedback,
  type RecommendationRequest,
  type RecommendationResult,
  type RecommendationRoute,
} from '../api/recommendation';
import { useAuthStore } from '../stores/auth';

const route = useRoute();
const authStore = useAuthStore();
const loading = ref(false);
const saving = ref(false);
const result = ref<RecommendationResult | null>(null);
const history = ref<Array<Record<string, any>>>([]);
const activeRouteName = ref('main');

const interestOptions = [
  { label: '历史文化', value: 'history' },
  { label: '自然风光', value: 'nature' },
  { label: '亲子休闲', value: 'family' },
  { label: '拍照打卡', value: 'photo' },
  { label: '室内展馆', value: 'indoor' },
  { label: '低强度慢游', value: 'relax' },
];
const intensityOptions = [
  { label: '低强度', value: 'low' },
  { label: '中等', value: 'medium' },
  { label: '高强度', value: 'high' },
];
const form = reactive<RecommendationRequest>({
  interests: ['history'],
  free_text: '',
  time_budget_minutes: 120,
  intensity: 'medium',
});

const routePresets = [
  { title: '历史文化深度游', detail: '约 4 小时 · 中等强度', interests: ['history'], duration: 240, intensity: 'medium', icon: History },
  { title: '自然风光轻松游', detail: '约 3 小时 · 低强度', interests: ['nature', 'photo'], duration: 180, intensity: 'low', icon: Trees },
  { title: '亲子家庭经典游', detail: '约 2.5 小时 · 低强度', interests: ['family', 'relax'], duration: 150, intensity: 'low', icon: Users },
];

function recommendationPayload(): RecommendationRequest {
  return {
    interests: [...form.interests],
    free_text: form.free_text,
    time_budget_minutes: form.time_budget_minutes,
    intensity: form.intensity,
  };
}

function applyPreset(preset: typeof routePresets[number]) {
  form.interests = [...preset.interests];
  form.time_budget_minutes = preset.duration;
  form.intensity = preset.intensity;
}

const routes = computed(() => {
  if (!result.value?.main_route) return [];
  return [
    { key: 'main', title: '主路线', route: result.value.main_route },
    ...(result.value.alternatives || []).map((route, index) => ({ key: `alt-${index}`, title: `备选 ${index + 1}`, route })),
  ];
});
const activeRoute = computed(() => routes.value.find((item) => item.key === activeRouteName.value)?.route || result.value?.main_route || null);

async function loadInitialData() {
  try {
    const [preferences, historyResult] = await Promise.all([getRecommendationPreferences(), listRecommendationHistory(8)]);
    Object.assign(form, preferences.preferences || {});
    history.value = historyResult.items || [];
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载推荐数据失败');
  }
}

async function handleRecommend() {
  loading.value = true;
  try {
    result.value = await createRecommendation(recommendationPayload());
    activeRouteName.value = 'main';
    await refreshHistory();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '生成推荐失败');
  } finally {
    loading.value = false;
  }
}

async function handleSavePreferences() {
  saving.value = true;
  try {
    await saveRecommendationPreferences(recommendationPayload());
    ElMessage.success('偏好已保存');
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '保存偏好失败');
  } finally {
    saving.value = false;
  }
}

async function handleClearPreferences() {
  await deleteRecommendationPreferences();
  ElMessage.success('偏好已清除');
}

async function refreshHistory() {
  const historyResult = await listRecommendationHistory(8);
  history.value = historyResult.items || [];
}

async function sendFeedback(action: string, rating?: number) {
  if (!result.value?.recommendation_id) return;
  await submitRecommendationFeedback({ recommendation_id: result.value.recommendation_id, action, rating });
  ElMessage.success('反馈已记录');
}

async function copyRoute(route: RecommendationRoute | null) {
  if (!route) return;
  const text = route.stops.map((stop) => `${stop.start_time}-${stop.end_time} ${stop.name}: ${stop.script}`).join('\n');
  await navigator.clipboard.writeText(text);
  ElMessage.success('路线话术已复制');
}

function exportRoute(route: RecommendationRoute | null) {
  if (!route) return;
  const blob = new Blob([JSON.stringify(route, null, 2)], { type: 'application/json;charset=utf-8' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = `${route.name}.json`;
  link.click();
  URL.revokeObjectURL(link.href);
}

function printRoute() {
  window.print();
}

function formatScore(route: RecommendationRoute | null) {
  return route ? Math.round(route.score * 100) : 0;
}

function nodeLabel(stop: RecommendationRoute['stops'][number]) {
  const labels: Record<string, string> = { start: '起点', end: '终点', path: '路径节点', draft: '待确认' };
  return labels[stop.node_type || ''] || '';
}

function isRecommendationPageActive(path: string) {
  if (path === '/app/recommendation') {
    return route.path === path;
  }
  return route.path === path || route.path.startsWith(`${path}/`);
}

onMounted(loadInitialData);
</script>

<template>
  <section class="recommendation-page" v-loading="loading">
    <div class="dashboard-title-row">
      <div>
        <h2>个性化游览推荐</h2>
      </div>
      <div class="dashboard-actions">
        <el-button :icon="RefreshCw" @click="loadInitialData">刷新</el-button>
        <el-button :icon="Save" :loading="saving" @click="handleSavePreferences">保存偏好</el-button>
        <el-button type="primary" :icon="Sparkles" :loading="loading" @click="handleRecommend">生成路线</el-button>
      </div>
    </div>

    <nav class="recommendation-page-tabs" aria-label="推荐功能导航">
      <RouterLink
        to="/app/recommendation"
        class="recommendation-page-tab"
        :class="{ 'is-active': isRecommendationPageActive('/app/recommendation') }"
      >
        <Route :size="16" aria-hidden="true" />
        <span>路线推荐</span>
      </RouterLink>
      <RouterLink
        v-if="authStore.isAdmin"
        to="/app/recommendation/manage"
        class="recommendation-page-tab"
        :class="{ 'is-active': isRecommendationPageActive('/app/recommendation/manage') }"
      >
        <Settings :size="16" aria-hidden="true" />
        <span>维护推荐</span>
      </RouterLink>
    </nav>

    <div class="recommendation-layout">
      <section class="chart-panel recommendation-form-panel">
        <h3>游客偏好</h3>
        <el-form label-position="top">
          <el-form-item label="兴趣标签">
            <el-select v-model="form.interests" multiple collapse-tags collapse-tags-tooltip>
              <el-option v-for="item in interestOptions" :key="item.value" :label="item.label" :value="item.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="补充描述">
            <el-input v-model="form.free_text" type="textarea" :rows="3" placeholder="例如：对历史感兴趣，同行老人较多。" />
          </el-form-item>
          <div class="recommendation-form-grid">
            <el-form-item label="游览时长"><el-input-number v-model="form.time_budget_minutes" :min="30" :max="480" :step="15" /></el-form-item>
            <el-form-item label="体力强度"><el-select v-model="form.intensity"><el-option v-for="item in intensityOptions" :key="item.value" :label="item.label" :value="item.value" /></el-select></el-form-item>
          </div>
          <el-button text type="danger" @click="handleClearPreferences">清除已保存偏好</el-button>
        </el-form>
      </section>

      <section class="recommendation-result-panel">
        <section v-if="!result?.main_route" class="recommendation-empty-state">
          <div class="recommendation-empty-copy">
            <span class="recommendation-empty-icon"><Sparkles :size="24" /></span>
            <p class="recommendation-empty-eyebrow">个性化路线</p>
            <h3>选择一种游览方式</h3>
            <p>根据兴趣、可用时间和体力偏好，从已维护路线中选出主路线与备选路线。</p>
          </div>
          <div class="recommendation-presets">
            <button v-for="preset in routePresets" :key="preset.title" type="button" @click="applyPreset(preset)">
              <component :is="preset.icon" :size="20" aria-hidden="true" />
              <span><strong>{{ preset.title }}</strong><small>{{ preset.detail }}</small></span>
            </button>
          </div>
          <div class="recommendation-empty-summary">
            <span>已选 {{ form.interests.length }} 个兴趣</span>
            <span>{{ form.time_budget_minutes }} 分钟</span>
            <el-button type="primary" :icon="Sparkles" :loading="loading" @click="handleRecommend">生成推荐路线</el-button>
          </div>
        </section>
        <template v-else>
          <div class="recommendation-route-tabs">
            <button v-for="item in routes" :key="item.key" type="button" :class="{ active: item.key === activeRouteName }" @click="activeRouteName = item.key">
              <Route :size="16" />{{ item.title }}
            </button>
          </div>

          <article v-if="activeRoute" class="chart-panel route-detail">
            <div class="route-head">
              <div>
                <span class="kpi-source">匹配度 {{ formatScore(activeRoute) }}</span>
                <h3>{{ activeRoute.name }}</h3>
                <p class="panel-note">{{ activeRoute.summary }}</p>
              </div>
              <div class="route-actions">
                <el-button :icon="Clipboard" @click="copyRoute(activeRoute)">复制话术</el-button>
                <el-button :icon="Printer" @click="printRoute">打印</el-button>
                <el-button :icon="Download" @click="exportRoute(activeRoute)">导出</el-button>
              </div>
            </div>
            <div class="route-meta">
              <span>{{ activeRoute.duration_minutes }} 分钟</span>
              <span>步行 {{ activeRoute.walk_minutes }} 分钟</span>
              <span>{{ activeRoute.intensity }}</span>
              <span v-if="activeRoute.budget_level">{{ activeRoute.budget_level }}</span>
            </div>
            <el-alert v-for="risk in activeRoute.risks" :key="risk" type="warning" show-icon :closable="false" :title="risk" />
            <el-timeline class="route-timeline">
              <el-timeline-item v-for="stop in activeRoute.stops" :key="stop.id" :timestamp="`${stop.start_time} - ${stop.end_time}`">
                <div class="route-stop" :class="{ 'route-stop-node': stop.score_eligible === false }">
                  <strong>
                    <span>{{ stop.name }}</span>
                    <em v-if="nodeLabel(stop)">{{ nodeLabel(stop) }}</em>
                  </strong>
                  <span v-if="stop.score_eligible !== false">{{ stop.category }} · 停留 {{ stop.stay_minutes }} 分钟 · 步行 {{ stop.walk_minutes }} 分钟</span>
                  <span v-else>{{ stop.category }}<template v-if="stop.stay_minutes"> · 停留 {{ stop.stay_minutes }} 分钟</template></span>
                  <p v-if="stop.explanation_focus">{{ stop.explanation_focus }}</p>
                  <blockquote v-if="stop.script">{{ stop.script }}</blockquote>
                </div>
              </el-timeline-item>
            </el-timeline>
            <div class="feedback-row">
              <el-button type="success" :icon="ThumbsUp" @click="sendFeedback('adopt', 5)">采纳路线</el-button>
              <el-button :icon="ThumbsDown" @click="sendFeedback('reject', 2)">不合适</el-button>
            </div>
          </article>

          <section class="chart-panel">
            <h3>推荐历史</h3>
            <el-table :data="history" height="220">
              <el-table-column label="路线" min-width="180">
                <template #default="{ row }">{{ row.result?.main_route?.name || '-' }}</template>
              </el-table-column>
              <el-table-column label="匹配度" width="90">
                <template #default="{ row }">{{ Math.round((row.score_breakdown?.total || 0) * 100) }}</template>
              </el-table-column>
            </el-table>
          </section>
        </template>
      </section>
    </div>
  </section>
</template>
