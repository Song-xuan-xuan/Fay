<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { Download, FileText, RefreshCw, Sparkles } from '@lucide/vue';
import {
  exportVisitorReport,
  generateVisitorReport,
  getLatestVisitorReport,
  getVisitorReport,
  getVisitorReportEvidence,
  listVisitorReports,
  updateVisitorReportActionStatus,
  type VisitorReport,
  type VisitorReportAction,
  type VisitorReportEvidence,
  type VisitorReportRange,
} from '../../api/dashboard';

const loading = ref(false);
const generating = ref(false);
const exporting = ref(false);
const selectedRange = ref<VisitorReportRange>('7d');
const report = ref<VisitorReport | null>(null);
const history = ref<VisitorReport[]>([]);
const evidence = ref<VisitorReportEvidence[]>([]);

const rangeOptions: Array<{ label: string; value: VisitorReportRange }> = [
  { label: '今日', value: 'today' },
  { label: '最近 7 天', value: '7d' },
  { label: '最近 30 天', value: '30d' },
  { label: '本周', value: 'week' },
  { label: '本月', value: 'month' },
];

const statusOptions: Array<{ label: string; value: VisitorReportAction['status'] }> = [
  { label: '待处理', value: 'pending' },
  { label: '处理中', value: 'processing' },
  { label: '已完成', value: 'done' },
  { label: '已忽略', value: 'ignored' },
];

const visitorReportActions = computed(() => report.value?.actions || report.value?.suggestions || []);
const metrics = computed(() => report.value?.metrics || null);
const topTopics = computed(() => metrics.value?.top_topics || []);
const sentiments = computed(() => toCountRows(metrics.value?.sentiments || {}));
const risks = computed(() => toCountRows(metrics.value?.risks || {}));

async function loadLatest() {
  loading.value = true;
  try {
    const latest = await getLatestVisitorReport();
    if ('id' in latest) {
      await loadReport(latest.id);
    }
    await loadHistory();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载游客感受度报告失败');
  } finally {
    loading.value = false;
  }
}

async function loadHistory() {
  const result = await listVisitorReports(20);
  history.value = result.items || [];
}

async function loadReport(id: number) {
  const [detail, evidenceResult] = await Promise.all([getVisitorReport(id), getVisitorReportEvidence(id)]);
  report.value = detail;
  evidence.value = evidenceResult.items || [];
}

async function handleGenerate() {
  generating.value = true;
  try {
    const generated = await generateVisitorReport({ range: selectedRange.value });
    report.value = generated;
    await Promise.all([loadReport(generated.id), loadHistory()]);
    ElMessage.success('游客感受度报告已生成');
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '生成报告失败');
  } finally {
    generating.value = false;
  }
}

async function handleExport(format: 'md' | 'html') {
  if (!report.value) return;
  exporting.value = true;
  try {
    const content = await exportVisitorReport(report.value.id, format);
    downloadText(content, `visitor-report-${report.value.id}.${format}`, format);
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '导出报告失败');
  } finally {
    exporting.value = false;
  }
}

async function handleActionStatus(action: VisitorReportAction, status: VisitorReportAction['status']) {
  const updated = await updateVisitorReportActionStatus(action.id, status);
  const target = visitorReportActions.value.find((item) => item.id === updated.id);
  if (target) {
    target.status = updated.status;
  }
}

function selectHistoryReport(row: VisitorReport) {
  loadReport(row.id);
}

function handleActionStatusChange(action: VisitorReportAction, value: string | number | boolean) {
  handleActionStatus(action, value as VisitorReportAction['status']).catch((error) => {
    ElMessage.error(error instanceof Error ? error.message : '更新建议状态失败');
  });
}

function toCountRows(source: Record<string, number>) {
  return Object.entries(source).map(([name, count]) => ({ name, count }));
}

function percent(value: number, total: number) {
  return `${Math.max(2, Math.round((Number(value || 0) / Math.max(1, total)) * 100))}%`;
}

function formatTime(timestamp?: number) {
  if (!timestamp) return '-';
  return new Date(timestamp * 1000).toLocaleString();
}

function downloadText(content: string, filename: string, format: 'md' | 'html') {
  const type = format === 'html' ? 'text/html;charset=utf-8' : 'text/markdown;charset=utf-8';
  const url = URL.createObjectURL(new Blob([content], { type }));
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

onMounted(loadLatest);
</script>

<template>
  <section class="visitor-report-panel" v-loading="loading">
    <div class="filter-row visitor-report-toolbar">
      <el-select v-model="selectedRange" class="range-select">
        <el-option v-for="item in rangeOptions" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
      <el-button type="primary" :icon="Sparkles" :loading="generating" @click="handleGenerate">生成报告</el-button>
      <el-button :icon="RefreshCw" :loading="loading" @click="loadLatest">刷新</el-button>
      <el-button :icon="Download" :disabled="!report" :loading="exporting" @click="handleExport('md')">导出 Markdown</el-button>
      <el-button :icon="FileText" :disabled="!report" :loading="exporting" @click="handleExport('html')">导出 HTML</el-button>
    </div>

    <el-empty v-if="!report" description="暂无游客感受度报告，请先生成。" />

    <template v-else>
      <div class="kpi-grid compact-kpis">
        <article class="kpi-card">
          <span class="kpi-source">交互记录</span>
          <strong>{{ metrics?.message_count || 0 }}<small>条</small></strong>
          <p>分析消息数</p>
        </article>
        <article class="kpi-card">
          <span class="kpi-source">情感识别</span>
          <strong>{{ Math.round((metrics?.negative_ratio || 0) * 100) }}<small>%</small></strong>
          <p>负面占比</p>
        </article>
        <article class="kpi-card">
          <span class="kpi-source">风险识别</span>
          <strong>{{ metrics?.complaint_count || 0 }}<small>条</small></strong>
          <p>投诉问题</p>
        </article>
        <article class="kpi-card">
          <span class="kpi-source">服务闭环</span>
          <strong>{{ metrics?.unresolved_count || 0 }}<small>条</small></strong>
          <p>疑似未解决</p>
        </article>
      </div>

      <div class="split-grid">
        <section class="chart-panel">
          <h3>关注点 TOP</h3>
          <div class="rank-list">
            <div v-for="item in topTopics" :key="item.topic" class="rank-row">
              <span>{{ item.topic }}</span><b>{{ item.count }}</b>
              <i :style="{ width: percent(item.count, metrics?.message_count || 1) }" />
            </div>
          </div>
        </section>
        <section class="chart-panel">
          <h3>情感与风险</h3>
          <div class="rank-list">
            <div v-for="item in sentiments" :key="`sentiment-${item.name}`" class="rank-row">
              <span>{{ item.name }}</span><b>{{ item.count }}</b>
              <i :style="{ width: percent(item.count, metrics?.message_count || 1) }" />
            </div>
            <div v-for="item in risks" :key="`risk-${item.name}`" class="rank-row">
              <span>风险 {{ item.name }}</span><b>{{ item.count }}</b>
              <i :style="{ width: percent(item.count, metrics?.message_count || 1) }" />
            </div>
          </div>
        </section>
      </div>

      <div class="split-grid">
        <section class="chart-panel">
          <h3>报告正文</h3>
          <p class="report-text">{{ report.report_text }}</p>
        </section>
        <section class="chart-panel">
          <h3>历史报告</h3>
          <el-table :data="history" height="260" @row-click="selectHistoryReport">
            <el-table-column prop="title" label="报告" min-width="180" />
            <el-table-column label="生成时间" width="170">
              <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
            </el-table-column>
          </el-table>
        </section>
      </div>

      <section class="chart-panel">
        <h3>服务建议待办</h3>
        <el-table :data="visitorReportActions" height="300">
          <el-table-column prop="title" label="建议" min-width="180" />
          <el-table-column prop="description" label="说明" min-width="260" />
          <el-table-column label="状态" width="150">
            <template #default="{ row }">
              <el-select :model-value="row.status" @change="handleActionStatusChange(row, $event)">
                <el-option v-for="item in statusOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </template>
          </el-table-column>
        </el-table>
      </section>

      <section class="chart-panel">
        <h3>原始依据</h3>
        <el-table :data="evidence" height="360">
          <el-table-column prop="topic" label="关注点" width="120" />
          <el-table-column prop="sentiment_label" label="情感" width="110" />
          <el-table-column prop="risk_level" label="风险" width="100" />
          <el-table-column prop="resolved_status" label="解决状态" width="120" />
          <el-table-column prop="evidence_text" label="游客原文" min-width="260" show-overflow-tooltip />
          <el-table-column prop="reply_text" label="数字人回复" min-width="260" show-overflow-tooltip />
        </el-table>
      </section>
    </template>
  </section>
</template>
