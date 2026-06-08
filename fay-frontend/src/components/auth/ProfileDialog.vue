<script setup lang="ts">
import { computed, ref } from 'vue';
import { ElMessage } from 'element-plus';
import { Camera, KeyRound } from '@lucide/vue';
import ChangePasswordDialog from './ChangePasswordDialog.vue';
import { useAuthStore } from '../../stores/auth';

const props = defineProps<{ visible: boolean }>();
const emit = defineEmits<{ (event: 'update:visible', value: boolean): void }>();

const DEFAULT_USER_AVATAR = '/static/images/User_send.png';
const MAX_AVATAR_SIZE = 2 * 1024 * 1024;

const authStore = useAuthStore();
const avatarInput = ref<HTMLInputElement | null>(null);
const uploading = ref(false);
const passwordVisible = ref(false);

const avatarSrc = computed(() => authStore.user?.avatar_path || DEFAULT_USER_AVATAR);
const roleText = computed(() => (authStore.user?.role === 'admin' ? '管理员' : '普通用户'));

function updateVisible(value: boolean) {
  emit('update:visible', value);
}

function openAvatarPicker() {
  avatarInput.value?.click();
}

async function handleAvatarChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  if (!file.type.startsWith('image/')) {
    ElMessage.error('请选择图片文件');
    input.value = '';
    return;
  }
  if (file.size > MAX_AVATAR_SIZE) {
    ElMessage.error('头像文件不能超过 2MB');
    input.value = '';
    return;
  }
  uploading.value = true;
  try {
    await authStore.uploadAvatar(file);
    ElMessage.success('头像已更新');
  } finally {
    uploading.value = false;
    input.value = '';
  }
}
</script>

<template>
  <el-dialog
    :model-value="props.visible"
    title="个人中心"
    width="520px"
    class="profile-dialog-shell"
    @update:model-value="updateVisible"
  >
    <div class="profile-dialog">
      <section class="profile-identity" aria-label="账户头像">
        <img class="profile-avatar-large" :src="avatarSrc" alt="用户头像" />
        <div class="profile-summary">
          <h3>{{ authStore.user?.username || 'User' }}</h3>
          <p>{{ roleText }}</p>
          <div class="profile-actions">
            <el-button :icon="Camera" :loading="uploading" @click="openAvatarPicker">上传头像</el-button>
            <input
              ref="avatarInput"
              class="profile-file-input"
              type="file"
              accept="image/png,image/jpeg,image/webp,image/gif"
              @change="handleAvatarChange"
            />
          </div>
        </div>
      </section>

      <dl class="profile-meta">
        <div>
          <dt>用户名</dt>
          <dd>{{ authStore.user?.username || '-' }}</dd>
        </div>
        <div>
          <dt>邮箱</dt>
          <dd>{{ authStore.user?.email || '未设置' }}</dd>
        </div>
        <div>
          <dt>用户 ID</dt>
          <dd>{{ authStore.user?.uid || '-' }}</dd>
        </div>
      </dl>

      <section class="profile-security" aria-label="账户安全">
        <div>
          <h4>账户安全</h4>
          <p>定期更新密码，避免多人共用同一账号。</p>
        </div>
        <el-button :icon="KeyRound" type="primary" plain @click="passwordVisible = true">修改密码</el-button>
      </section>
    </div>

    <template #footer>
      <el-button type="primary" @click="updateVisible(false)">完成</el-button>
    </template>
  </el-dialog>

  <ChangePasswordDialog v-model:visible="passwordVisible" @success="passwordVisible = false" />
</template>

<style scoped>
.profile-dialog {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.profile-identity {
  display: flex;
  align-items: center;
  gap: 18px;
  border-bottom: 1px solid var(--color-border-light);
  padding-bottom: 20px;
}

.profile-avatar-large {
  width: 88px;
  height: 88px;
  flex: 0 0 auto;
  border-radius: 50%;
  object-fit: cover;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.12);
}

.profile-summary {
  min-width: 0;
}

.profile-summary h3,
.profile-security h4 {
  margin: 0;
}

.profile-summary p,
.profile-security p {
  margin: 6px 0 0;
  color: var(--color-text-secondary);
  font-size: 14px;
}

.profile-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 14px;
}

.profile-file-input {
  display: none;
}

.profile-meta {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin: 0;
}

.profile-meta div {
  min-width: 0;
  border: 1px solid var(--color-border-light);
  border-radius: 8px;
  padding: 12px;
}

.profile-meta dt {
  color: var(--color-text-secondary);
  font-size: 12px;
}

.profile-meta dd {
  overflow: hidden;
  margin: 6px 0 0;
  color: var(--color-text-primary);
  font-size: 14px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.profile-security {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  border-top: 1px solid var(--color-border-light);
  padding-top: 18px;
}

@media (max-width: 640px) {
  .profile-identity,
  .profile-security {
    align-items: flex-start;
    flex-direction: column;
  }

  .profile-meta {
    grid-template-columns: 1fr;
  }
}
</style>
