<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { CheckCircle2, ExternalLink, FolderSync, ImagePlus, Monitor, Pencil, Plus, Search, Trash2 } from '@lucide/vue';
import { createDigitalHuman, deleteDigitalHuman, importLive2dResourceHumans, uploadDigitalHumanCover } from '../api/digitalHumans';
import DigitalHumanEditor from '../components/digital-humans/DigitalHumanEditor.vue';
import { useAppStore } from '../stores/app';
import { useLive2dStore } from '../stores/live2d';
import type { DigitalHuman, DigitalHumanPayload, DigitalHumanType } from '../types';

const appStore = useAppStore();
const live2d = useLive2dStore();
const loading = ref(false);
const saving = ref(false);
const importing = ref(false);
const editorVisible = ref(false);
const previewVisible = ref(false);
const editingId = ref('');
const previewHuman = ref<DigitalHuman | null>(null);
const coverTargetId = ref('');
const coverInput = ref<HTMLInputElement | null>(null);

const form = reactive<DigitalHumanPayload>({
  name: '',
  type: 'live2d',
  cover_url: '',
  render_url: '',
  voice: '',
  tags: [],
  persona: {},
  enabled: true,
});
const tagText = ref('');

const typeOptions: Array<{ label: string; value: DigitalHumanType | '' }> = [
  { label: '全部类型', value: '' },
  { label: 'Live2D', value: 'live2d' },
  { label: '网页 iframe', value: 'iframe' },
  { label: '图片/GIF', value: 'image' },
];

const activeName = computed(() => live2d.activeHuman?.name || '未设置');
const activeTypeLabel = computed(() => typeLabel(live2d.activeHuman?.type));

function typeLabel(type?: DigitalHumanType | '') {
  if (type === 'live2d') return 'Live2D';
  if (type === 'iframe') return 'iframe';
  if (type === 'image') return '图片/GIF';
  return '未知';
}

function personaSummary(human: DigitalHuman) {
  const persona = human.persona || {};
  return [persona.position, persona.goal, persona.job, persona.additional].filter(Boolean).join(' · ') || '未填写人设摘要';
}

function resetForm() {
  editingId.value = '';
  Object.assign(form, {
    name: '',
    type: 'live2d',
    cover_url: '',
    render_url: '',
    voice: appStore.voiceList[0]?.value || '',
    tags: [],
    persona: {},
    enabled: true,
  });
  tagText.value = '';
}

function openCreate() {
  resetForm();
  editorVisible.value = true;
}

function openEdit(human: DigitalHuman) {
  editingId.value = human.id;
  Object.assign(form, {
    name: human.name,
    type: human.type,
    cover_url: human.cover_url,
    render_url: human.render_url,
    voice: human.voice,
    tags: [...(human.tags || [])],
    persona: { ...(human.persona || {}) },
    enabled: human.enabled,
  });
  tagText.value = (human.tags || []).join(', ');
  editorVisible.value = true;
}

async function loadDigitalHumans() {
  loading.value = true;
  try {
    await live2d.loadDigitalHumans();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '加载数字人失败');
  } finally {
    loading.value = false;
  }
}

async function searchDigitalHumans() {
  await loadDigitalHumans();
}

function buildPayload(): DigitalHumanPayload {
  return {
    ...form,
    tags: tagText.value.split(',').map((item) => item.trim()).filter(Boolean),
    persona: { ...(form.persona || {}) },
  };
}

async function saveDigitalHuman() {
  saving.value = true;
  try {
    if (editingId.value) {
      await live2d.saveDigitalHuman(editingId.value, buildPayload());
    } else {
      const result = await createDigitalHuman(buildPayload());
      live2d.receiveDigitalHuman(result.digital_human);
    }
    editorVisible.value = false;
    ElMessage.success('数字人已保存');
    await loadDigitalHumans();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '保存数字人失败');
  } finally {
    saving.value = false;
  }
}

async function importLocalLive2dHumans() {
  importing.value = true;
  try {
    const result = await importLive2dResourceHumans();
    await loadDigitalHumans();
    if (result.imported.length) {
      ElMessage.success(`已导入 ${result.imported.length} 个本地 Live2D 形象`);
    } else {
      ElMessage.info('本地 Live2D 形象已在数字人库中');
    }
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '导入本地形象失败');
  } finally {
    importing.value = false;
  }
}

async function activateHuman(human: DigitalHuman) {
  await ElMessageBox.confirm(
    '新对话和后续生成将立即使用该数字人配置，正在生成或播放的内容不会被强制中断。',
    `设为当前：${human.name}`,
    { type: 'warning', confirmButtonText: '设为当前', cancelButtonText: '取消' },
  );
  try {
    await live2d.activateDigitalHuman(human.id);
    ElMessage.success('当前数字人已切换');
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '切换数字人失败');
  }
}

async function removeHuman(human: DigitalHuman) {
  await ElMessageBox.confirm(`确认删除数字人「${human.name}」？`, '删除数字人', { type: 'warning' });
  try {
    await deleteDigitalHuman(human.id);
    ElMessage.success('数字人已删除');
    await loadDigitalHumans();
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '删除数字人失败');
  }
}

function openPreview(human: DigitalHuman) {
  previewHuman.value = human;
  previewVisible.value = true;
}

function openCoverUpload(human: DigitalHuman) {
  coverTargetId.value = human.id;
  coverInput.value?.click();
}

async function handleCoverChange(file: File) {
  const targetId = coverTargetId.value || editingId.value;
  if (!file || !targetId) {
    return;
  }
  try {
    const result = await uploadDigitalHumanCover(targetId, file);
    form.cover_url = result.cover_url;
    live2d.receiveDigitalHuman(result.digital_human);
    ElMessage.success('封面已上传');
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '上传封面失败');
  } finally {
    coverTargetId.value = '';
  }
}

function handleCoverInputChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = '';
  if (file) {
    handleCoverChange(file);
  }
}

onMounted(loadDigitalHumans);
</script>

<template>
  <section class="live2d-page digital-human-library" v-loading="loading">
    <div class="panel digital-human-toolbar">
      <div>
        <h2>数字人库</h2>
        <p>当前：{{ activeName }} · {{ activeTypeLabel }}</p>
      </div>
      <div class="toolbar-actions digital-human-actions">
        <el-input
          v-model="live2d.keyword"
          :prefix-icon="Search"
          placeholder="搜索名称、人设、声音、标签"
          clearable
          @keyup.enter="searchDigitalHumans"
          @clear="searchDigitalHumans"
        />
        <el-select v-model="live2d.typeFilter" aria-label="数字人类型" @change="searchDigitalHumans">
          <el-option v-for="item in typeOptions" :key="item.label" :label="item.label" :value="item.value" />
        </el-select>
        <el-button :icon="Search" @click="searchDigitalHumans">搜索</el-button>
        <el-button :icon="FolderSync" :loading="importing" @click="importLocalLive2dHumans">导入本地形象</el-button>
        <el-button :icon="Plus" type="primary" @click="openCreate">新增</el-button>
      </div>
    </div>

    <div class="digital-human-grid">
      <article
        v-for="human in live2d.items"
        :key="human.id"
        class="digital-human-card"
        :class="{ active: human.id === live2d.activeId }"
      >
        <div class="human-cover">
          <img :src="human.cover_url || '/static/images/Normal.gif'" :alt="human.name" />
          <span v-if="human.id === live2d.activeId" class="active-badge">
            <CheckCircle2 :size="14" aria-hidden="true" /> 当前
          </span>
        </div>
        <div class="human-card-body">
          <div class="human-title-row">
            <h3>{{ human.name }}</h3>
            <span>{{ typeLabel(human.type) }}</span>
          </div>
          <p class="human-summary">{{ personaSummary(human) }}</p>
          <p class="human-voice">{{ human.voice || '未设置声音' }}</p>
          <div class="human-tags">
            <span v-for="tag in human.tags" :key="tag">{{ tag }}</span>
          </div>
        </div>
        <div class="human-card-actions">
          <el-button size="small" :icon="Monitor" @click="openPreview(human)">预览</el-button>
          <el-button size="small" :icon="Pencil" @click="openEdit(human)">编辑</el-button>
          <el-button size="small" :icon="ImagePlus" @click="openCoverUpload(human)">封面</el-button>
          <el-button size="small" type="primary" :disabled="human.id === live2d.activeId" @click="activateHuman(human)">
            设为当前
          </el-button>
          <el-button size="small" :icon="Trash2" :disabled="human.id === live2d.activeId" @click="removeHuman(human)" />
        </div>
      </article>
      <div v-if="!live2d.items.length" class="panel digital-human-empty">
        <h3>没有匹配的数字人</h3>
        <p>调整关键词或新增一个数字人。</p>
        <el-button :icon="Plus" type="primary" @click="openCreate">新增数字人</el-button>
      </div>
    </div>

    <input
      ref="coverInput"
      class="visually-hidden-input"
      type="file"
      accept="image/png,image/jpeg,image/webp,image/gif"
      @change="handleCoverInputChange"
    />

    <DigitalHumanEditor
      v-model:visible="editorVisible"
      v-model:tag-text="tagText"
      :editing="Boolean(editingId)"
      :form="form"
      :saving="saving"
      :voice-list="appStore.voiceList"
      @save="saveDigitalHuman"
      @cover-change="handleCoverChange"
    />

    <el-dialog v-model="previewVisible" :title="previewHuman?.name || '预览'" width="72vw" class="digital-human-preview-dialog">
      <div v-if="previewHuman" class="digital-human-preview">
        <iframe
          v-if="previewHuman.type !== 'image'"
          :src="previewHuman.render_url"
          title="数字人预览"
          sandbox="allow-scripts allow-same-origin"
        />
        <img v-else :src="previewHuman.cover_url" :alt="previewHuman.name" />
      </div>
      <template #footer>
        <el-button v-if="previewHuman?.render_url" :icon="ExternalLink" tag="a" :href="previewHuman.render_url" target="_blank">新窗口打开</el-button>
        <el-button @click="previewVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </section>
</template>
