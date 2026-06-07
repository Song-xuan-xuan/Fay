<script setup lang="ts">
import type { UserRecord } from '../../types';

defineProps<{
  visible: boolean;
  loading: boolean;
  saving: boolean;
  user: UserRecord | null;
  extraInfo: string;
  userPortrait: string;
}>();

const emit = defineEmits<{
  (name: 'update:visible', value: boolean): void;
  (name: 'update:extraInfo', value: string): void;
  (name: 'update:userPortrait', value: string): void;
  (name: 'save'): void;
}>();

function displayName(user: UserRecord | null): string {
  if (!user) {
    return '';
  }
  return user[1] === 'User' ? '主人' : user[1];
}
</script>

<template>
  <el-dialog
    :model-value="visible"
    :title="`编辑用户信息 - ${displayName(user)}`"
    width="600px"
    :close-on-click-modal="false"
    @update:model-value="emit('update:visible', $event)"
  >
    <div v-loading="loading" class="user-info-form">
      <label class="field-label">用户补充信息</label>
      <el-input
        :model-value="extraInfo"
        type="textarea"
        placeholder="请输入用户补充信息，例如：喜好、特征、注意事项等"
        :rows="4"
        maxlength="500"
        show-word-limit
        @update:model-value="emit('update:extraInfo', $event)"
      />
      <p class="field-hint">此信息会附加到对话提示词中，帮助 AI 更好地了解该用户。</p>

      <label class="field-label">用户画像 <span>每晚 22:35 自动分析更新</span></label>
      <el-input
        :model-value="userPortrait"
        type="textarea"
        placeholder="用户画像由系统根据对话内容自动分析生成，也可手动编辑"
        :rows="6"
        maxlength="1000"
        show-word-limit
        @update:model-value="emit('update:userPortrait', $event)"
      />
    </div>
    <template #footer>
      <el-button @click="emit('update:visible', false)">取消</el-button>
      <el-button type="primary" :loading="saving" @click="emit('save')">保存</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.user-info-form {
  display: grid;
  gap: 10px;
}

.field-label {
  color: #344054;
  font-weight: 600;
}

.field-label span,
.field-hint {
  color: #667085;
  font-size: 0.82rem;
  font-weight: 400;
}
</style>
