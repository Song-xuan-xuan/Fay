<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Play, Save, Square, Trash2, WandSparkles } from '@lucide/vue';
import { clearMemory, getData, startGenagents, submitConfig } from '../../api/setting';
import { BRAND_NAME, BRAND_SERVICE_NAME } from '../../config/brand';
import { useAppStore } from '../../stores/app';
import type { FayConfig } from '../../types';

const visible = defineModel<boolean>('visible', { required: true });
const appStore = useAppStore();
const loading = ref(false);

const form = reactive({
  qna: '',
  wakeWordEnabled: false,
  wakeWord: '',
  wakeWordType: 'common',
  playSound: false,
  recordEnabled: false,
  perceptionFollow: 0,
  memoryIsolateByUser: false,
  automaticPlayerStatus: false,
  automaticPlayerUrl: '',
});

const liveButtonText = computed(() => {
  if (appStore.liveState === 1) return '关闭';
  if (appStore.liveState === 2) return '正在开启';
  if (appStore.liveState === 3) return '正在关闭';
  return '开启';
});

function hydrate(config: FayConfig) {
  const source = config.source || {};
  const interact = config.interact || {};
  const record = source.record || {};
  const perception = interact.perception || {};
  const memory = config.memory || {};

  form.qna = interact.QnA || '';
  form.wakeWordEnabled = Boolean(source.wake_word_enabled);
  form.wakeWord = source.wake_word || '';
  form.wakeWordType = source.wake_word_type || 'common';
  form.playSound = Boolean(interact.playSound);
  form.recordEnabled = Boolean(record.enabled);
  form.perceptionFollow = Number(perception.follow || 0);
  form.memoryIsolateByUser = Boolean(memory.isolate_by_user);
  form.automaticPlayerStatus = Boolean(source.automatic_player_status);
  form.automaticPlayerUrl = source.automatic_player_url || '';
}

function toConfig(): FayConfig {
  return {
    source: {
      record: { enabled: form.recordEnabled },
      wake_word_enabled: form.wakeWordEnabled,
      wake_word: form.wakeWord,
      wake_word_type: form.wakeWordType,
      automatic_player_status: form.automaticPlayerStatus,
      automatic_player_url: form.automaticPlayerUrl,
    },
    interact: {
      playSound: form.playSound,
      QnA: form.qna,
      perception: { follow: form.perceptionFollow },
    },
    memory: {
      isolate_by_user: form.memoryIsolateByUser,
    },
  };
}

async function loadConfig() {
  loading.value = true;
  try {
    const data = await getData();
    hydrate(data.config);
  } finally {
    loading.value = false;
  }
}

async function saveConfig() {
  await submitConfig(toConfig());
  ElMessage.success('交互设置已保存');
}

async function toggleLive() {
  if (appStore.liveState === 1) {
    await appStore.stopLive();
  } else {
    await appStore.startLive();
  }
}

async function handleClearMemory() {
  await ElMessageBox.confirm(`清除记忆会删除 ${BRAND_NAME} 的对话记忆，需重启后完全生效。确认继续？`, '清除记忆', { type: 'warning' });
  const result = await clearMemory();
  if (result.success) {
    ElMessage.success(result.message);
  } else {
    ElMessage.error(result.message);
  }
}

async function clonePersonality() {
  if (appStore.liveState !== 1) {
    ElMessage.warning(`请先开启 ${BRAND_SERVICE_NAME}`);
    return;
  }
  const { value } = await ElMessageBox.prompt('请输入克隆要求', '克隆人格', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    inputPlaceholder: '例如：你现在是一个活泼开朗的助手...',
    inputValidator: (input) => Boolean(input?.trim()) || '克隆要求不能为空',
  });
  const result = await startGenagents(value.trim());
  if (result.success) {
    await ElMessageBox.alert(
      `决策分析页面已启动，请复制以下链接在新窗口中打开：<br><br><code>${result.url || ''}</code>`,
      '克隆人格',
      { dangerouslyUseHTMLString: true },
    );
  } else {
    ElMessage.error(result.message || '启动决策分析页面失败');
  }
}

watch(visible, (isVisible) => {
  if (isVisible) {
    loadConfig();
  }
});
</script>

<template>
  <el-drawer v-model="visible" title="交互设置" size="520px" append-to-body>
    <div class="interaction-settings-drawer" v-loading="loading">
      <div class="drawer-actions">
        <el-button :icon="Save" type="primary" :disabled="!appStore.configEditable" @click="saveConfig">保存设置</el-button>
        <el-button :icon="appStore.liveState === 1 ? Square : Play" @click="toggleLive">{{ liveButtonText }}</el-button>
      </div>

      <el-form label-position="top" class="settings-form compact-settings-form" :disabled="!appStore.configEditable">
        <div class="form-section">
          <h3>问答与唤醒</h3>
          <div class="form-grid">
            <el-form-item label="Q&A 文件"><el-input v-model="form.qna" /></el-form-item>
            <el-form-item label="唤醒词"><el-input v-model="form.wakeWord" /></el-form-item>
            <el-form-item label="唤醒方式">
              <el-select v-model="form.wakeWordType">
                <el-option label="普通" value="common" />
                <el-option label="前置词" value="front" />
              </el-select>
            </el-form-item>
          </div>
          <div class="switch-grid">
            <el-switch v-model="form.wakeWordEnabled" active-text="唤醒模式" />
            <el-switch v-model="form.playSound" active-text="服务器扬声器" />
            <el-switch v-model="form.recordEnabled" active-text="服务器麦克风" />
            <el-switch v-model="form.memoryIsolateByUser" active-text="认知隔离" />
          </div>
          <el-form-item label="敏感度">
            <el-slider v-model="form.perceptionFollow" />
          </el-form-item>
        </div>

        <div class="form-section">
          <h3>自动播报</h3>
          <div class="form-grid">
            <el-form-item label="状态"><el-switch v-model="form.automaticPlayerStatus" /></el-form-item>
            <el-form-item label="地址"><el-input v-model="form.automaticPlayerUrl" placeholder="http://127.0.0.1:6000" /></el-form-item>
          </div>
        </div>
      </el-form>

      <div class="danger-zone compact-danger-zone">
        <el-button :icon="Trash2" @click="handleClearMemory">清除记忆</el-button>
        <el-button :icon="WandSparkles" @click="clonePersonality">克隆人格</el-button>
      </div>
    </div>
  </el-drawer>
</template>
