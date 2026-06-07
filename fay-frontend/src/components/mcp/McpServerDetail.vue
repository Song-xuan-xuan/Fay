<script setup lang="ts">
import { computed } from 'vue';
import { Edit3, Plug, Power, RefreshCw, Wrench } from '@lucide/vue';
import type { McpResource, McpServer, McpTool } from '../../api/mcp';

const props = defineProps<{
  server: McpServer | null;
  tools: McpTool[];
  resources: McpResource[];
  toolsLoading: boolean;
  resourcesLoading: boolean;
  actionKey: string;
  toolActionKey: string;
  resourceActionKey: string;
}>();

const emit = defineEmits<{
  edit: [server: McpServer];
  connect: [server: McpServer];
  restart: [server: McpServer];
  refreshTools: [server: McpServer];
  toggleTool: [tool: McpTool, enabled: boolean];
  toggleResource: [resource: McpResource, enabled: boolean];
}>();

const enabledToolCount = computed(() => props.tools.filter((tool) => tool.enabled !== false).length);
const enabledResourceCount = computed(() => props.resources.filter((item) => item.enabled !== false).length);

function statusType(status?: string) {
  if (status === 'online') return 'success';
  if (status === 'connecting') return 'warning';
  return 'info';
}

function isAction(action: string, serverId?: number) {
  return Boolean(serverId) && props.actionKey === `${action}:${serverId}`;
}

function endpoint(server: McpServer) {
  if (server.transport === 'stdio') return server.command || '--';
  return server.ip || '--';
}

function argsText(args?: string[]) {
  return Array.isArray(args) && args.length ? args.join(' ') : '--';
}

function schemaSummary(tool: McpTool) {
  const schema = tool.inputSchema || {};
  const keys = Object.keys(schema);
  return keys.length ? keys.join(', ') : '--';
}

function handleToolToggle(tool: McpTool, value: string | number | boolean) {
  emit('toggleTool', tool, Boolean(value));
}

function handleResourceToggle(resource: McpResource, value: string | number | boolean) {
  emit('toggleResource', resource, Boolean(value));
}
</script>

<template>
  <section class="mcp-section mcp-detail">
    <template v-if="server">
      <div class="mcp-detail-title">
        <div>
          <h3>{{ server.name }}</h3>
          <p>{{ endpoint(server) }}</p>
        </div>
        <div class="mcp-detail-actions">
          <el-tag :type="statusType(server.status)">{{ server.status || 'offline' }}</el-tag>
          <el-button :icon="Edit3" @click="emit('edit', server)">编辑</el-button>
          <el-button
            :icon="server.status === 'online' ? Power : Plug"
            :type="server.status === 'online' ? 'warning' : 'primary'"
            :loading="isAction(server.status === 'online' ? 'disconnect' : 'connect', server.id)"
            @click="emit('connect', server)"
          >
            {{ server.status === 'online' ? '断开' : '连接' }}
          </el-button>
          <el-button :icon="RefreshCw" :loading="isAction('restart', server.id)" @click="emit('restart', server)">
            刷新连接
          </el-button>
        </div>
      </div>

      <div class="mcp-meta-grid">
        <div><span>ID</span><strong>{{ server.id }}</strong></div>
        <div><span>Transport</span><strong>{{ server.transport || 'sse' }}</strong></div>
        <div><span>Latency</span><strong>{{ server.latency || '--' }}</strong></div>
        <div><span>Autostart</span><strong>{{ server.autostart ? '是' : '否' }}</strong></div>
        <div class="wide"><span>Connection time</span><strong>{{ server.connection_time || '--' }}</strong></div>
        <div class="wide"><span>Args</span><strong>{{ argsText(server.args) }}</strong></div>
        <div class="wide"><span>CWD</span><strong>{{ server.cwd || '--' }}</strong></div>
      </div>

      <div class="mcp-table-block">
        <div class="mcp-section-header compact">
          <div>
            <h3>工具</h3>
            <p>{{ enabledToolCount }} / {{ tools.length }} enabled</p>
          </div>
          <el-button :icon="Wrench" :loading="toolsLoading" @click="emit('refreshTools', server)">刷新工具</el-button>
        </div>
        <el-table :data="tools" v-loading="toolsLoading" empty-text="暂无可用工具" height="260">
          <el-table-column label="工具" min-width="180">
            <template #default="{ row }">
              <div class="mcp-tool-name">
                <span>{{ row.name }}</span>
                <el-tag v-if="row.prestart" size="small" type="warning">预启动</el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="描述" min-width="260" prop="description" show-overflow-tooltip />
          <el-table-column label="Schema" width="150">
            <template #default="{ row }">{{ schemaSummary(row) }}</template>
          </el-table-column>
          <el-table-column label="启用" width="92" align="right">
            <template #default="{ row }">
              <el-switch
                :model-value="row.enabled !== false"
                :loading="toolActionKey === row.name"
                @change="handleToolToggle(row, $event)"
              />
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="mcp-table-block">
        <div class="mcp-section-header compact">
          <div>
            <h3>Resources</h3>
            <p>{{ enabledResourceCount }} / {{ resources.length }} 注入 prompt</p>
          </div>
        </div>
        <el-table :data="resources" v-loading="resourcesLoading" empty-text="暂无 MCP resources" height="220">
          <el-table-column label="名称" min-width="160" prop="name" show-overflow-tooltip />
          <el-table-column label="URI" min-width="260" prop="uri" show-overflow-tooltip />
          <el-table-column label="注入" width="92" align="right">
            <template #default="{ row }">
              <el-switch
                :model-value="row.enabled !== false"
                :loading="resourceActionKey === row.uri"
                @change="handleResourceToggle(row, $event)"
              />
            </template>
          </el-table-column>
        </el-table>
      </div>
    </template>
    <div v-else class="mcp-empty-state">请选择一个 MCP server。</div>
  </section>
</template>
