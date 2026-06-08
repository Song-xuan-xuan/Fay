<script setup lang="ts">
import { reactive, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { useAuthStore } from '../../stores/auth';

const props = withDefaults(defineProps<{ visible: boolean; force?: boolean }>(), { force: false });
const emit = defineEmits<{ (event: 'update:visible', value: boolean): void; (event: 'success'): void }>();

const authStore = useAuthStore();
const loading = ref(false);
const form = reactive({ oldPassword: '', newPassword: '', confirmPassword: '' });

function closeDialog() {
  if (!props.force) emit('update:visible', false);
}

async function submitPassword() {
  if (form.newPassword.length < 8) {
    ElMessage.error('新密码至少 8 位');
    return;
  }
  if (form.newPassword !== form.confirmPassword) {
    ElMessage.error('两次输入的新密码不一致');
    return;
  }
  loading.value = true;
  try {
    await authStore.changePassword(form.oldPassword, form.newPassword);
    ElMessage.success('密码已修改');
    emit('success');
    emit('update:visible', false);
    form.oldPassword = '';
    form.newPassword = '';
    form.confirmPassword = '';
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <el-dialog
    :model-value="visible"
    title="修改密码"
    width="420px"
    :show-close="!force"
    :close-on-click-modal="!force"
    :close-on-press-escape="!force"
    @update:model-value="closeDialog"
  >
    <el-form label-position="top">
      <el-form-item label="当前密码">
        <el-input v-model="form.oldPassword" type="password" show-password autocomplete="current-password" />
      </el-form-item>
      <el-form-item label="新密码">
        <el-input v-model="form.newPassword" type="password" show-password autocomplete="new-password" />
      </el-form-item>
      <el-form-item label="确认新密码">
        <el-input v-model="form.confirmPassword" type="password" show-password autocomplete="new-password" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button v-if="!force" @click="closeDialog">取消</el-button>
      <el-button type="primary" :loading="loading" @click="submitPassword">保存</el-button>
    </template>
  </el-dialog>
</template>
