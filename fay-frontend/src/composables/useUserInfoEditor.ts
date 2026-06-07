import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import {
  getUserExtraInfo,
  getUserPortrait,
  updateUserExtraInfo,
  updateUserPortrait,
} from '../api/message';
import type { UserRecord } from '../types';

export function useUserInfoEditor() {
  const visible = ref(false);
  const loading = ref(false);
  const saving = ref(false);
  const editingUser = ref<UserRecord | null>(null);
  const extraInfo = ref('');
  const userPortrait = ref('');

  async function openUserInfoDialog(user: UserRecord) {
    editingUser.value = user;
    extraInfo.value = '';
    userPortrait.value = '';
    visible.value = true;
    loading.value = true;
    try {
      const [extraInfoResult, portraitResult] = await Promise.all([
        getUserExtraInfo(user[1]),
        getUserPortrait(user[1]),
      ]);
      extraInfo.value = extraInfoResult.success ? extraInfoResult.extra_info || '' : '';
      userPortrait.value = portraitResult.success ? portraitResult.user_portrait || '' : '';
    } catch (error) {
      ElMessage.error(error instanceof Error ? error.message : '获取用户信息失败');
    } finally {
      loading.value = false;
    }
  }

  async function saveUserInfo() {
    if (!editingUser.value) {
      return;
    }
    saving.value = true;
    try {
      const username = editingUser.value[1];
      const [extraInfoResult, portraitResult] = await Promise.all([
        updateUserExtraInfo(username, extraInfo.value),
        updateUserPortrait(username, userPortrait.value),
      ]);
      if (extraInfoResult.success && portraitResult.success) {
        visible.value = false;
        ElMessage.success('用户信息已保存');
      } else {
        ElMessage.error('部分信息保存失败');
      }
    } catch (error) {
      ElMessage.error(error instanceof Error ? error.message : '保存用户信息时出错');
    } finally {
      saving.value = false;
    }
  }

  return {
    visible,
    loading,
    saving,
    editingUser,
    extraInfo,
    userPortrait,
    openUserInfoDialog,
    saveUserInfo,
  };
}
