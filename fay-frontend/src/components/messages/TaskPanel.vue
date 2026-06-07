<script setup lang="ts">
import type { ExecutionStatus } from '../../types';

defineProps<{
  execution: ExecutionStatus;
}>();
</script>

<template>
  <aside class="panel task-panel">
    <div class="panel-header">
      <h2>后台任务</h2>
    </div>
    <el-tag :type="execution.status === 'running' ? 'warning' : 'info'">{{ execution.status || 'idle' }}</el-tag>
    <p class="task-title">{{ execution.original_request || '暂无后台任务' }}</p>
    <ol v-if="execution.progress_messages?.length" class="task-log">
      <li v-for="item in execution.progress_messages" :key="item">{{ item }}</li>
    </ol>
  </aside>
</template>
