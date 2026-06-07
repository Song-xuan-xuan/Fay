<script setup lang="ts">
import { Plus, Trash2 } from '@lucide/vue';
import type { UserRecord } from '../../types';

defineProps<{
  users: UserRecord[];
  selectedUser: UserRecord | null;
  newUsername: string;
}>();

const emit = defineEmits<{
  (event: 'update:newUsername', value: string): void;
  (event: 'select', user: UserRecord): void;
  (event: 'edit', user: UserRecord): void;
  (event: 'remove', user: UserRecord): void;
  (event: 'add'): void;
}>();

function chooseUser(user: UserRecord, selectedUser: UserRecord | null) {
  if (selectedUser?.[0] === user[0]) {
    emit('edit', user);
    return;
  }
  emit('select', user);
}
</script>

<template>
  <aside class="panel user-panel">
    <div class="panel-header">
      <h2>会话用户</h2>
    </div>
    <div class="user-list">
      <button
        v-for="user in users"
        :key="user[0]"
        class="user-row"
        :class="{ active: selectedUser?.[0] === user[0] }"
        type="button"
        @click="chooseUser(user, selectedUser)"
      >
        <span>{{ user[1] === 'User' ? '主人' : user[1] }}</span>
        <Trash2
          v-if="user[1] !== 'User'"
          :size="16"
          aria-label="删除用户"
          @click.stop="emit('remove', user)"
        />
      </button>
    </div>
    <div class="inline-form">
      <el-input
        :model-value="newUsername"
        placeholder="新用户"
        @update:model-value="emit('update:newUsername', $event)"
        @keyup.enter="emit('add')"
      />
      <el-button :icon="Plus" aria-label="添加用户" @click="emit('add')" />
    </div>
  </aside>
</template>
