<script setup lang="ts">
import { reactive, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { RefreshCw, Search, Trash2 } from '@lucide/vue';
import { cleanupAuditLogs, getAuditLogs } from '../../api/users';
import type { AuditLogRecord } from '../../types/auth';

const DEFAULT_RETENTION_DAYS = 90;
const ACTION_OPTIONS = [
  { label: '全部操作', value: '' },
  { label: '登录成功', value: 'login_success' },
  { label: '登录失败', value: 'login_failed' },
  { label: '退出登录', value: 'logout' },
  { label: '用户注册', value: 'register' },
  { label: '创建用户', value: 'user_create' },
  { label: '更新用户', value: 'user_update' },
  { label: '删除用户', value: 'user_delete' },
  { label: '修改密码', value: 'password_change' },
  { label: '重置密码', value: 'password_reset' },
  { label: '更新头像', value: 'avatar_update' },
];

const visible = ref(false);
const loading = ref(false);
const cleanupLoading = ref(false);
const auditLogs = ref<AuditLogRecord[]>([]);
const total = ref(0);
const query = reactive({
  action: '',
  username: '',
  page: 1,
  pageSize: 10,
});

function formatTime(timestamp?: number | null) {
  if (!timestamp) return '-';
  return new Date(timestamp * 1000).toLocaleString();
}

function actionLabel(action: string) {
  return ACTION_OPTIONS.find((option) => option.value === action)?.label || action;
}

function formatDetails(details?: Record<string, unknown>) {
  if (!details || Object.keys(details).length === 0) return '-';
  return Object.entries(details).map(([key, value]) => {
    const formatted = typeof value === 'object' ? JSON.stringify(value) : String(value);
    return `${key}: ${formatted}`;
  }).join('，');
}

async function loadAuditLogs() {
  loading.value = true;
  try {
    const result = await getAuditLogs({
      action: query.action || undefined,
      username: query.username.trim() || undefined,
      page: query.page,
      pageSize: query.pageSize,
    });
    auditLogs.value = result.list || [];
    total.value = result.total || 0;
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载审核日志失败');
  } finally {
    loading.value = false;
  }
}

function open() {
  visible.value = true;
  query.page = 1;
  loadAuditLogs();
}

function refreshIfOpen() {
  if (visible.value) {
    loadAuditLogs();
  }
}

function handleSearch() {
  query.page = 1;
  loadAuditLogs();
}

function handlePageSizeChange() {
  query.page = 1;
  loadAuditLogs();
}

async function handleCleanup() {
  try {
    await ElMessageBox.confirm(
      `将删除 ${DEFAULT_RETENTION_DAYS} 天前的审核日志，近期日志会保留。确认继续？`,
      '清理审核日志',
      { type: 'warning', confirmButtonText: '清理', cancelButtonText: '取消' },
    );
  } catch {
    return;
  }
  cleanupLoading.value = true;
  try {
    const result = await cleanupAuditLogs(DEFAULT_RETENTION_DAYS);
    ElMessage.success(`已清理 ${result.deleted} 条审核日志`);
    query.page = 1;
    await loadAuditLogs();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '清理审核日志失败');
  } finally {
    cleanupLoading.value = false;
  }
}

defineExpose({ open, refreshIfOpen });
</script>

<template>
  <el-drawer v-model="visible" title="审核日志" size="min(760px, 100vw)" class="audit-drawer" append-to-body>
    <div class="audit-toolbar">
      <el-input
        v-model="query.username"
        class="audit-filter-username"
        clearable
        placeholder="按用户名筛选"
        @clear="handleSearch"
        @keyup.enter="handleSearch"
      />
      <el-select v-model="query.action" class="audit-filter-action" @change="handleSearch">
        <el-option v-for="option in ACTION_OPTIONS" :key="option.value" :label="option.label" :value="option.value" />
      </el-select>
      <el-button :icon="Search" type="primary" @click="handleSearch">查询</el-button>
      <el-button :icon="RefreshCw" :loading="loading" @click="loadAuditLogs">刷新</el-button>
      <el-button :icon="Trash2" :loading="cleanupLoading" type="danger" plain @click="handleCleanup">清理旧日志</el-button>
    </div>

    <el-table :data="auditLogs" class="audit-table" v-loading="loading" empty-text="暂无审核日志">
      <el-table-column label="操作" width="112">
        <template #default="{ row }">
          <el-tag size="small" effect="plain">{{ actionLabel(row.action) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="用户" min-width="120" show-overflow-tooltip>
        <template #default="{ row }">{{ row.username || '系统' }}</template>
      </el-table-column>
      <el-table-column label="详情" min-width="240" show-overflow-tooltip>
        <template #default="{ row }">
          <span class="audit-table-details">{{ formatDetails(row.details) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="资源" min-width="120" show-overflow-tooltip>
        <template #default="{ row }">{{ row.resource || '-' }}</template>
      </el-table-column>
      <el-table-column label="IP" width="130" show-overflow-tooltip>
        <template #default="{ row }">{{ row.ip_address || '-' }}</template>
      </el-table-column>
      <el-table-column label="时间" width="170">
        <template #default="{ row }">{{ formatTime(row.timestamp) }}</template>
      </el-table-column>
    </el-table>

    <div class="audit-pagination">
      <el-pagination
        v-model:current-page="query.page"
        v-model:page-size="query.pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        background
        layout="total, sizes, prev, pager, next"
        @current-change="loadAuditLogs"
        @size-change="handlePageSizeChange"
      />
    </div>
  </el-drawer>
</template>
