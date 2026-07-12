<script setup lang="ts">
import { computed, onMounted, ref, type CSSProperties } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Check, ImagePlus, Link as LinkIcon, RefreshCw, Trash2, Upload } from '@lucide/vue';
import {
  activateBackground,
  addBackgroundUrl,
  deleteBackground,
  uploadBackground,
  type BackgroundItem,
} from '../../api/backgrounds';
import { useBackgroundStore } from '../../stores/background';

const backgroundStore = useBackgroundStore();
const fileInput = ref<HTMLInputElement | null>(null);
const selectedFile = ref<File | null>(null);
const uploadName = ref('');
const backgroundUrl = ref('');
const urlName = ref('');
const actionKey = ref('');

const canUpload = computed(() => Boolean(selectedFile.value && !actionKey.value));
const canAddUrl = computed(() => Boolean(backgroundUrl.value.trim() && !actionKey.value));

function previewStyle(background: BackgroundItem): CSSProperties {
  return {
    backgroundImage: `url("${background.url.replace(/"/g, '\\"')}")`,
  };
}

function errorText(error: unknown, fallback: string) {
  return error instanceof Error ? error.message : fallback;
}

function chooseFile() {
  fileInput.value?.click();
}

function selectFile(event: Event) {
  const input = event.target as HTMLInputElement;
  selectedFile.value = input.files?.[0] || null;
  if (selectedFile.value && !uploadName.value.trim()) {
    uploadName.value = selectedFile.value.name.replace(/\.[^.]+$/, '');
  }
}

async function refreshBackgrounds() {
  await backgroundStore.loadBackgrounds();
}

async function uploadSelected() {
  if (!selectedFile.value) {
    ElMessage.warning('请选择背景图文件');
    return;
  }
  actionKey.value = 'upload';
  try {
    const result = await uploadBackground(selectedFile.value, uploadName.value);
    await refreshBackgrounds();
    backgroundStore.selectBackground(result.background.id);
    selectedFile.value = null;
    uploadName.value = '';
    if (fileInput.value) fileInput.value.value = '';
    ElMessage.success('背景图已上传');
  } catch (error) {
    ElMessage.error(errorText(error, '上传背景图失败'));
  } finally {
    actionKey.value = '';
  }
}

async function addUrlBackground() {
  if (!backgroundUrl.value.trim()) {
    ElMessage.warning('请输入背景图 URL');
    return;
  }
  actionKey.value = 'add-url';
  try {
    const result = await addBackgroundUrl(backgroundUrl.value, urlName.value);
    await refreshBackgrounds();
    backgroundStore.selectBackground(result.background.id);
    backgroundUrl.value = '';
    urlName.value = '';
    ElMessage.success('URL 背景已添加');
  } catch (error) {
    ElMessage.error(errorText(error, '添加 URL 背景失败'));
  } finally {
    actionKey.value = '';
  }
}

async function setGlobalBackground(background: BackgroundItem) {
  actionKey.value = `activate:${background.id}`;
  try {
    await activateBackground(background.id);
    await refreshBackgrounds();
    backgroundStore.selectBackground(background.id);
    ElMessage.success('全局背景已更新');
  } catch (error) {
    ElMessage.error(errorText(error, '设置全局背景失败'));
  } finally {
    actionKey.value = '';
  }
}

function useLocalBackground(background: BackgroundItem) {
  backgroundStore.selectBackground(background.id);
  ElMessage.success('本机背景已切换');
}

async function removeBackground(background: BackgroundItem) {
  try {
    await ElMessageBox.confirm(`确认删除 ${background.name}？`, '删除背景图', { type: 'warning' });
  } catch {
    return;
  }
  actionKey.value = `delete:${background.id}`;
  try {
    await deleteBackground(background.id);
    if (backgroundStore.activeId === background.id) {
      backgroundStore.useDefaultBackground();
    }
    await refreshBackgrounds();
    ElMessage.success('背景图已删除');
  } catch (error) {
    ElMessage.error(errorText(error, '删除背景图失败'));
  } finally {
    actionKey.value = '';
  }
}

onMounted(() => {
  refreshBackgrounds().catch(() => undefined);
});
</script>

<template>
  <section class="background-manager">
    <div class="background-manager-head">
      <div>
        <h3>背景管理</h3>
        <p>上传本地背景图或添加在线 URL，并设置页面默认背景。</p>
      </div>
      <el-button :icon="RefreshCw" :loading="backgroundStore.loading" @click="refreshBackgrounds">刷新</el-button>
    </div>

    <div class="background-upload-section">
      <h4>上传本地图片</h4>
      <div class="background-upload-row">
        <input
          ref="fileInput"
          class="background-file-input"
          type="file"
          accept="image/png,image/jpeg,image/webp,image/gif"
          @change="selectFile"
        />
        <el-input v-model="uploadName" placeholder="背景名称" />
        <el-button :icon="ImagePlus" @click="chooseFile">
          {{ selectedFile?.name || '选择图片' }}
        </el-button>
        <el-button :icon="Upload" type="primary" :disabled="!canUpload" :loading="actionKey === 'upload'" @click="uploadSelected">
          上传
        </el-button>
      </div>
    </div>

    <div class="background-url-section">
      <h4>添加 URL 背景</h4>
      <div class="background-upload-row">
        <el-input v-model="urlName" placeholder="背景名称" />
        <el-input v-model="backgroundUrl" placeholder="粘贴背景图片 URL（http:// 或 https://）" clearable />
        <el-button :icon="LinkIcon" type="primary" :disabled="!canAddUrl" :loading="actionKey === 'add-url'" @click="addUrlBackground">
          添加
        </el-button>
      </div>
    </div>

    <div class="background-grid" v-loading="backgroundStore.loading">
      <article
        v-for="background in backgroundStore.backgrounds.filter(bg => !bg.builtin)"
        :key="background.id"
        class="background-card"
        :class="{ 'is-active': background.url === backgroundStore.activeBackgroundUrl }"
      >
        <div class="background-card-preview" :style="previewStyle(background)" />
        <div class="background-card-copy">
          <strong>{{ background.name }}</strong>
          <span v-if="background.builtin">内置背景</span>
          <span v-else-if="background.url_type">URL 背景</span>
          <span v-else>已上传</span>
        </div>
        <div class="background-card-actions">
          <el-button size="small" :icon="Check" @click="setGlobalBackground(background)">设为全局</el-button>
          <el-button size="small" @click="useLocalBackground(background)">本机使用</el-button>
          <el-button
            v-if="!background.builtin"
            size="small"
            :icon="Trash2"
            :loading="actionKey === `delete:${background.id}`"
            @click="removeBackground(background)"
          >
            删除
          </el-button>
        </div>
      </article>
    </div>
  </section>
</template>
