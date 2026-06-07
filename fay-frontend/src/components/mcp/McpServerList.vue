<script setup lang="ts">
import { Cable, Edit3, Plug, Power, RefreshCw, Trash2 } from '@lucide/vue';
import type { McpServer } from '../../api/mcp';

const props = defineProps<{
  servers: McpServer[];
  selectedId: number | null;
  loading: boolean;
  actionKey: string;
}>();

const emit = defineEmits<{
  select: [serverId: number];
  connect: [server: McpServer];
  restart: [server: McpServer];
  edit: [server: McpServer];
  delete: [server: McpServer];
}>();

function statusType(status?: string) {
  if (status === 'online') return 'success';
  if (status === 'connecting') return 'warning';
  return 'info';
}

function transportLabel(server: McpServer) {
  return server.transport === 'stdio' ? 'stdio' : 'sse';
}

function isAction(action: string, serverId: number) {
  return props.actionKey === `${action}:${serverId}`;
}

function rowClassName({ row }: { row: McpServer }) {
  return row.id === props.selectedId ? 'mcp-row-active' : '';
}

function handleRowClick(row: McpServer) {
  emit('select', row.id);
}
</script>

<template>
  <section class="mcp-section mcp-server-list">
    <div class="mcp-section-header">
      <div>
        <h3>Server 列表</h3>
        <p>{{ servers.length }} 个 MCP server</p>
      </div>
      <el-tag type="info">{{ servers.filter((item) => item.status === 'online').length }} online</el-tag>
    </div>

    <el-table
      :data="servers"
      :row-class-name="rowClassName"
      v-loading="loading"
      empty-text="暂无 MCP server"
      height="520"
      @row-click="handleRowClick"
    >
      <el-table-column label="名称" min-width="180">
        <template #default="{ row }">
          <div class="mcp-server-name">
            <Cable :size="16" aria-hidden="true" />
            <span>{{ row.name }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="传输" width="86">
        <template #default="{ row }">{{ transportLabel(row) }}</template>
      </el-table-column>
      <el-table-column label="状态" width="106">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ row.status || 'offline' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="246" align="right">
        <template #default="{ row }">
          <el-button
            :icon="row.status === 'online' ? Power : Plug"
            text
            :type="row.status === 'online' ? 'warning' : 'primary'"
            :loading="isAction(row.status === 'online' ? 'disconnect' : 'connect', row.id)"
            @click.stop="emit('connect', row)"
          >
            {{ row.status === 'online' ? '断开' : '连接' }}
          </el-button>
          <el-button :icon="RefreshCw" text :loading="isAction('restart', row.id)" @click.stop="emit('restart', row)">
            刷新
          </el-button>
          <el-button :icon="Edit3" text @click.stop="emit('edit', row)">编辑</el-button>
          <el-button :icon="Trash2" text type="danger" :loading="isAction('delete', row.id)" @click.stop="emit('delete', row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </section>
</template>
