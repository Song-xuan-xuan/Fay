<script setup lang="ts">
import { Pencil, Plus, Trash2 } from '@lucide/vue';
import type { ChatSession } from '../../api/message';

defineProps<{
  sessions: ChatSession[];
  selectedSession: ChatSession | null;
  loading?: boolean;
}>();

const emit = defineEmits<{
  (event: 'select', session: ChatSession): void;
  (event: 'create'): void;
  (event: 'rename', session: ChatSession): void;
  (event: 'remove', session: ChatSession): void;
}>();

function titleOf(session: ChatSession) {
  return session.title?.trim() || '未命名会话';
}
</script>

<template>
  <aside class="panel user-panel session-panel">
    <div class="panel-header session-panel-header">
      <h2>我的会话</h2>
      <el-button
        :icon="Plus"
        circle
        :loading="loading"
        aria-label="新建会话"
        title="新建会话"
        @click="emit('create')"
      />
    </div>

    <div class="session-list">
      <button
        v-for="session in sessions"
        :key="session.id"
        class="session-row"
        :class="{ active: selectedSession?.id === session.id }"
        type="button"
        @click="emit('select', session)"
      >
        <span class="session-copy">
          <span class="session-title">{{ titleOf(session) }}</span>
          <span class="session-meta">{{ Number(session.message_count || 0) }} 条</span>
        </span>
        <span class="session-actions" @click.stop>
          <button
            class="icon-button"
            type="button"
            :disabled="session.id === 0"
            aria-label="重命名会话"
            title="重命名会话"
            @click="emit('rename', session)"
          >
            <Pencil :size="16" aria-hidden="true" />
          </button>
          <button
            class="icon-button danger"
            type="button"
            aria-label="删除会话"
            title="删除会话"
            @click="emit('remove', session)"
          >
            <Trash2 :size="16" aria-hidden="true" />
          </button>
        </span>
      </button>
      <p v-if="sessions.length === 0 && !loading" class="session-empty">暂无会话</p>
    </div>
  </aside>
</template>
