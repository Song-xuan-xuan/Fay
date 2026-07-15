<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Image as ImageIcon, Plus, RefreshCw, Server } from '@lucide/vue';
import BackgroundManager from '../components/backgrounds/BackgroundManager.vue';
import McpServerDetail from '../components/mcp/McpServerDetail.vue';
import McpServerDialog from '../components/mcp/McpServerDialog.vue';
import McpServerList from '../components/mcp/McpServerList.vue';
import {
  connectMcpServer,
  createMcpServer,
  deleteMcpServer,
  disconnectMcpServer,
  getMcpServerResources,
  getMcpServerTools,
  listMcpServers,
  toggleMcpResource,
  toggleMcpTool,
  updateMcpServer,
  type McpResource,
  type McpServer,
  type McpServerPayload,
  type McpTool,
} from '../api/mcp';

type SettingsView = 'mcp' | 'backgrounds';

const servers = ref<McpServer[]>([]);
const tools = ref<McpTool[]>([]);
const resources = ref<McpResource[]>([]);
const selectedId = ref<number | null>(null);
const loadingServers = ref(false);
const toolsLoading = ref(false);
const resourcesLoading = ref(false);
const savingDialog = ref(false);
const dialogVisible = ref(false);
const editingServer = ref<McpServer | null>(null);
const actionKey = ref('');
const toolActionKey = ref('');
const resourceActionKey = ref('');
const activeSettingsView = ref<SettingsView>('mcp');

const selectedServer = computed(() => servers.value.find((server) => server.id === selectedId.value) || null);
const onlineCount = computed(() => servers.value.filter((server) => server.status === 'online').length);
const mcpApiHost = computed(() => `${window.location.origin}/api/mcp`);

function errorText(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

function syncServer(updated?: McpServer) {
  if (!updated) return;
  const index = servers.value.findIndex((server) => server.id === updated.id);
  if (index >= 0) servers.value.splice(index, 1, updated);
}

function chooseSelectedServer(nextServers: McpServer[], keepSelection: boolean) {
  const currentExists = nextServers.some((server) => server.id === selectedId.value);
  if (!keepSelection || !currentExists) selectedId.value = nextServers[0]?.id ?? null;
}

async function loadTools(server: McpServer) {
  toolsLoading.value = true;
  try {
    const data = await getMcpServerTools(server.id);
    tools.value = data.success ? data.tools || [] : [];
    if (!data.success && data.message) ElMessage.warning(data.message);
  } catch (error) {
    tools.value = [];
    ElMessage.error(errorText(error, '加载工具失败'));
  } finally {
    toolsLoading.value = false;
  }
}

async function loadResources(server: McpServer) {
  resourcesLoading.value = true;
  try {
    const data = await getMcpServerResources(server.id);
    resources.value = data.success ? data.resources || [] : [];
  } catch (error) {
    resources.value = [];
    ElMessage.error(errorText(error, '加载 Resources 失败'));
  } finally {
    resourcesLoading.value = false;
  }
}

async function loadSelectedDetail(server = selectedServer.value) {
  if (!server || server.status !== 'online') {
    tools.value = [];
    resources.value = [];
    return;
  }
  await Promise.all([loadTools(server), loadResources(server)]);
}

async function loadServers(keepSelection = true) {
  loadingServers.value = true;
  try {
    const data = await listMcpServers();
    servers.value = Array.isArray(data) ? data : [];
    chooseSelectedServer(servers.value, keepSelection);
    await loadSelectedDetail();
  } catch (error) {
    ElMessage.error(errorText(error, '加载 MCP server 失败'));
  } finally {
    loadingServers.value = false;
  }
}

function selectServer(serverId: number) {
  selectedId.value = serverId;
  loadSelectedDetail().catch(() => undefined);
}

async function connectOrDisconnect(server: McpServer) {
  const online = server.status === 'online';
  actionKey.value = `${online ? 'disconnect' : 'connect'}:${server.id}`;
  try {
    const result = online ? await disconnectMcpServer(server.id) : await connectMcpServer(server.id);
    syncServer(result.server);
    await loadServers();
    ElMessage.success(result.message || (online ? '已断开连接' : '已连接'));
  } catch (error) {
    ElMessage.error(errorText(error, online ? '断开失败' : '连接失败'));
  } finally {
    actionKey.value = '';
  }
}

async function restartServer(server: McpServer) {
  actionKey.value = `restart:${server.id}`;
  try {
    if (server.status === 'online') await disconnectMcpServer(server.id);
    const result = await connectMcpServer(server.id);
    syncServer(result.server);
    await loadServers();
    ElMessage.success(result.message || '连接已刷新');
  } catch (error) {
    ElMessage.error(errorText(error, '刷新连接失败'));
  } finally {
    actionKey.value = '';
  }
}

function openCreateDialog() {
  editingServer.value = null;
  dialogVisible.value = true;
}

function openEditDialog(server: McpServer) {
  editingServer.value = { ...server, args: Array.isArray(server.args) ? [...server.args] : [] };
  dialogVisible.value = true;
}

async function saveServer(payload: McpServerPayload) {
  savingDialog.value = true;
  try {
    const result = editingServer.value
      ? await updateMcpServer(editingServer.value.id, payload)
      : await createMcpServer(payload);
    if (result.server) selectedId.value = result.server.id;
    dialogVisible.value = false;
    await loadServers(false);
    ElMessage.success(result.message || '配置已保存');
  } catch (error) {
    ElMessage.error(errorText(error, '保存失败'));
  } finally {
    savingDialog.value = false;
  }
}

async function removeServer(server: McpServer) {
  try {
    await ElMessageBox.confirm(`确认删除 ${server.name}？`, '删除 MCP Server', { type: 'warning' });
  } catch {
    return;
  }
  actionKey.value = `delete:${server.id}`;
  try {
    const result = await deleteMcpServer(server.id);
    selectedId.value = selectedId.value === server.id ? null : selectedId.value;
    await loadServers(false);
    ElMessage.success(result.message || '已删除');
  } catch (error) {
    ElMessage.error(errorText(error, '删除失败'));
  } finally {
    actionKey.value = '';
  }
}

async function changeToolState(tool: McpTool, enabled: boolean) {
  const server = selectedServer.value;
  if (!server) return;
  toolActionKey.value = tool.name;
  try {
    const result = await toggleMcpTool(server.id, tool.name, enabled);
    tools.value = result.tools || tools.value.map((item) => (item.name === tool.name ? { ...item, enabled } : item));
    ElMessage.success(result.message || '工具状态已更新');
  } catch (error) {
    ElMessage.error(errorText(error, '工具状态更新失败'));
  } finally {
    toolActionKey.value = '';
  }
}

async function changeResourceState(resource: McpResource, enabled: boolean) {
  const server = selectedServer.value;
  if (!server) return;
  resourceActionKey.value = resource.uri;
  try {
    await toggleMcpResource(server.id, resource.uri, enabled);
    resources.value = resources.value.map((item) => (item.uri === resource.uri ? { ...item, enabled } : item));
    ElMessage.success('Resource 状态已更新');
  } catch (error) {
    ElMessage.error(errorText(error, 'Resource 状态更新失败'));
  } finally {
    resourceActionKey.value = '';
  }
}

onMounted(() => {
  loadServers(false).catch(() => undefined);
});
</script>

<template>
  <section class="panel mcp-panel">
    <div class="panel-header settings-page-header">
      <div>
        <h2>系统设置</h2>
      </div>
      <div v-if="activeSettingsView === 'mcp'" class="header-actions">
        <el-button :icon="RefreshCw" :loading="loadingServers" @click="loadServers()">刷新</el-button>
        <el-button :icon="Plus" type="primary" @click="openCreateDialog">添加</el-button>
      </div>
    </div>

    <div class="settings-view-switch-row">
      <el-radio-group v-model="activeSettingsView" class="settings-view-switch" aria-label="设置分类">
        <el-radio-button label="mcp">
          <span class="settings-view-option">
            <Server :size="17" aria-hidden="true" />
            <span>MCP 服务</span>
          </span>
        </el-radio-button>
        <el-radio-button label="backgrounds">
          <span class="settings-view-option">
            <ImageIcon :size="17" aria-hidden="true" />
            <span>壁纸库</span>
          </span>
        </el-radio-button>
      </el-radio-group>
    </div>

    <BackgroundManager v-show="activeSettingsView === 'backgrounds'" class="mcp-background-manager" />

    <div v-show="activeSettingsView === 'mcp'" class="mcp-layout">
      <McpServerList
        :servers="servers"
        :selected-id="selectedId"
        :loading="loadingServers"
        :action-key="actionKey"
        @select="selectServer"
        @connect="connectOrDisconnect"
        @restart="restartServer"
        @edit="openEditDialog"
        @delete="removeServer"
      />
      <McpServerDetail
        :server="selectedServer"
        :tools="tools"
        :resources="resources"
        :tools-loading="toolsLoading"
        :resources-loading="resourcesLoading"
        :action-key="actionKey"
        :tool-action-key="toolActionKey"
        :resource-action-key="resourceActionKey"
        @edit="openEditDialog"
        @connect="connectOrDisconnect"
        @restart="restartServer"
        @refresh-tools="loadSelectedDetail"
        @toggle-tool="changeToolState"
        @toggle-resource="changeResourceState"
      />
    </div>

    <McpServerDialog v-model:visible="dialogVisible" :server="editingServer" :saving="savingDialog" @save="saveServer" />
  </section>
</template>
