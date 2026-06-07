<script setup lang="ts">
defineProps<{
  selectedCount: number;
}>();

const emit = defineEmits<{
  (name: 'select-all'): void;
  (name: 'clear'): void;
  (name: 'preview'): void;
  (name: 'exit'): void;
}>();
</script>

<template>
  <div class="share-toolbar">
    <span>已选 {{ selectedCount }} 条</span>
    <el-button size="small" @click="emit('select-all')">全选</el-button>
    <el-button size="small" @click="emit('clear')">取消全选</el-button>
    <el-button size="small" type="primary" :disabled="selectedCount === 0" @click="emit('preview')">预览</el-button>
    <el-button size="small" @click="emit('exit')">退出</el-button>
  </div>
</template>
