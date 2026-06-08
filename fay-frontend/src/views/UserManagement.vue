<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Plus, RefreshCw, RotateCcw, Trash2 } from '@lucide/vue';
import { createUser, deleteUserById, getAuditLogs, getUsers, resetUserPassword, updateUser } from '../api/users';
import type { AuditLogRecord, AuthRole, ManagedUser } from '../types/auth';

const DEFAULT_USER_AVATAR = '/static/images/User_send.png';
const RECENT_LOGIN_SECONDS = 7 * 24 * 60 * 60;

const loading = ref(false);
const users = ref<ManagedUser[]>([]);
const auditLogs = ref<AuditLogRecord[]>([]);
const createVisible = ref(false);
const createForm = reactive({ username: '', password: '', role: 'user' as AuthRole, email: '' });

const activeUsers = computed(() => users.value.filter((user) => Number(user.is_active ?? 1) === 1).length);
const adminUsers = computed(() => users.value.filter((user) => user.role === 'admin').length);
const recentLoginUsers = computed(() => {
  const now = Date.now() / 1000;
  return users.value.filter((user) => user.last_login && now - user.last_login < RECENT_LOGIN_SECONDS).length;
});

function formatTime(timestamp?: number | null) {
  if (!timestamp) return '-';
  return new Date(timestamp * 1000).toLocaleString();
}

function avatarFor(path?: string) {
  return path || DEFAULT_USER_AVATAR;
}

function actionLabel(action: string) {
  const labels: Record<string, string> = {
    avatar_update: '更新头像',
    login_failed: '登录失败',
    login_success: '登录成功',
    logout: '退出登录',
    password_change: '修改密码',
    password_reset: '重置密码',
    register: '用户注册',
    user_create: '创建用户',
    user_delete: '删除用户',
    user_update: '更新用户',
  };
  return labels[action] || action;
}

function formatDetails(details?: Record<string, unknown>) {
  if (!details || Object.keys(details).length === 0) return '-';
  return Object.entries(details).map(([key, value]) => {
    const formatted = typeof value === 'object' ? JSON.stringify(value) : String(value);
    return `${key}: ${formatted}`;
  }).join('，');
}

async function loadUsers() {
  loading.value = true;
  try {
    const result = await getUsers();
    users.value = result.list || [];
  } finally {
    loading.value = false;
  }
}

async function loadAuditLogs() {
  const result = await getAuditLogs('', 20);
  auditLogs.value = result.list || [];
}

async function handleCreateUser() {
  if (!createForm.username.trim() || createForm.password.length < 8) {
    ElMessage.error('用户名不能为空，密码至少 8 位');
    return;
  }
  await createUser({ ...createForm, username: createForm.username.trim() });
  ElMessage.success('用户已创建');
  createVisible.value = false;
  createForm.username = '';
  createForm.password = '';
  createForm.role = 'user';
  createForm.email = '';
  await Promise.all([loadUsers(), loadAuditLogs()]);
}

async function changeRole(user: ManagedUser, role: AuthRole) {
  await updateUser(user.uid, { role });
  ElMessage.success('角色已更新');
  await loadUsers();
}

async function toggleActive(user: ManagedUser, isActive: boolean) {
  await updateUser(user.uid, { is_active: isActive });
  ElMessage.success(isActive ? '用户已启用' : '用户已禁用');
  await loadUsers();
}

async function resetPassword(user: ManagedUser) {
  const { value } = await ElMessageBox.prompt('请输入新密码', `重置 ${user.username} 的密码`, {
    inputType: 'password',
    inputValidator: (value) => (value.length >= 8 ? true : '密码至少 8 位'),
  });
  await resetUserPassword(user.uid, value);
  ElMessage.success('密码已重置');
  await loadAuditLogs();
}

async function removeUser(user: ManagedUser) {
  await ElMessageBox.confirm(`确认删除用户 ${user.username}？`, '删除用户', { type: 'warning' });
  await deleteUserById(user.uid);
  ElMessage.success('用户已删除');
  await Promise.all([loadUsers(), loadAuditLogs()]);
}

onMounted(() => {
  Promise.all([loadUsers(), loadAuditLogs()]).catch(() => undefined);
});
</script>

<template>
  <section class="panel users-panel">
    <div class="panel-header">
      <div>
        <h2>用户管理</h2>
        <p>管理账号状态、角色、密码与最近审计记录</p>
      </div>
      <div class="header-actions">
        <el-button :icon="RefreshCw" :loading="loading" @click="loadUsers">刷新</el-button>
        <el-button :icon="Plus" type="primary" @click="createVisible = true">新建用户</el-button>
      </div>
    </div>

    <div class="user-summary-grid">
      <div class="user-summary-item">
        <span>用户总数</span>
        <strong>{{ users.length }}</strong>
      </div>
      <div class="user-summary-item">
        <span>启用中</span>
        <strong>{{ activeUsers }}</strong>
      </div>
      <div class="user-summary-item">
        <span>管理员</span>
        <strong>{{ adminUsers }}</strong>
      </div>
      <div class="user-summary-item">
        <span>近 7 天登录</span>
        <strong>{{ recentLoginUsers }}</strong>
      </div>
    </div>

    <el-table :data="users" class="users-table" v-loading="loading">
      <el-table-column label="用户" min-width="220">
        <template #default="{ row }">
          <div class="user-cell">
            <img class="user-avatar" :src="avatarFor(row.avatar_path)" alt="" />
            <div class="user-cell-copy">
              <strong>{{ row.username }}</strong>
              <span>{{ row.email || '未设置邮箱' }}</span>
            </div>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="角色" width="150">
        <template #default="{ row }">
          <el-select :model-value="row.role" size="small" @change="(role: AuthRole) => changeRole(row, role)">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="130">
        <template #default="{ row }">
          <el-switch :model-value="Number(row.is_active ?? 1) === 1" @change="(value: boolean) => toggleActive(row, value)" />
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="180">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="最后登录" width="180">
        <template #default="{ row }">{{ formatTime(row.last_login) }}</template>
      </el-table-column>
      <el-table-column label="改密时间" width="180">
        <template #default="{ row }">{{ formatTime(row.password_changed_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="190" fixed="right">
        <template #default="{ row }">
          <el-button :icon="RotateCcw" text @click="resetPassword(row)">重置</el-button>
          <el-button :icon="Trash2" text type="danger" @click="removeUser(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <section class="audit-list" aria-label="最近审计">
      <div class="audit-list-header">
        <div>
          <h3>最近审计</h3>
          <p>展示登录、用户变更、密码和头像相关操作</p>
        </div>
        <el-button size="small" :icon="RefreshCw" @click="loadAuditLogs">刷新审计</el-button>
      </div>
      <div v-if="auditLogs.length === 0" class="audit-empty">暂无审计记录</div>
      <div v-for="log in auditLogs" :key="log.id" class="audit-item">
        <span class="audit-action">{{ actionLabel(log.action) }}</span>
        <div class="audit-main">
          <strong>{{ log.username || '系统' }}</strong>
          <span>{{ formatDetails(log.details) }}</span>
          <small>{{ log.resource || '-' }} · {{ log.ip_address || '-' }}</small>
        </div>
        <time>{{ formatTime(log.timestamp) }}</time>
      </div>
    </section>

    <el-dialog v-model="createVisible" title="新建用户" width="460px">
      <el-form label-position="top">
        <el-form-item label="用户名"><el-input v-model="createForm.username" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="createForm.password" type="password" show-password /></el-form-item>
        <el-form-item label="角色">
          <el-select v-model="createForm.role">
            <el-option label="管理员" value="admin" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
        <el-form-item label="邮箱"><el-input v-model="createForm.email" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCreateUser">创建</el-button>
      </template>
    </el-dialog>
  </section>
</template>
