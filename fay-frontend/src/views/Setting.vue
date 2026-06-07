<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { Play, Save, Square, Trash2, WandSparkles } from '@lucide/vue';
import { clearMemory, getData, startGenagents, submitConfig } from '../api/setting';
import type { FayConfig } from '../types';
import { useAppStore } from '../stores/app';

const appStore = useAppStore();
const loading = ref(false);
const form = reactive({
  name: '',
  gender: '',
  age: '',
  birth: '',
  zodiac: '',
  constellation: '',
  position: '客服',
  goal: '解决问题',
  job: '',
  contact: '',
  additional: '',
  voice: '',
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

const positionOptions = ['客服', '陪伴', '教培', '娱乐', '销售', '助理'];
const goalOptions = ['解决问题', '陪伴情感', '提供知识', '促成交易', '工作协助'];

const liveButtonText = computed(() => {
  if (appStore.liveState === 1) return '关闭';
  if (appStore.liveState === 2) return '正在开启';
  if (appStore.liveState === 3) return '正在关闭';
  return '开启';
});

function hydrate(config: FayConfig) {
  const attribute = config.attribute || {};
  const source = config.source || {};
  const interact = config.interact || {};
  const record = source.record || {};
  const perception = interact.perception || {};
  const memory = config.memory || {};

  form.name = attribute.name || '';
  form.gender = attribute.gender || '';
  form.age = attribute.age || '';
  form.birth = attribute.birth || '';
  form.zodiac = attribute.zodiac || '';
  form.constellation = attribute.constellation || '';
  form.position = attribute.position || '客服';
  form.goal = attribute.goal || '解决问题';
  form.job = attribute.job || '';
  form.contact = attribute.contact || '';
  form.additional = attribute.additional || '';
  form.voice = attribute.voice || '';
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
    attribute: {
      voice: form.voice,
      name: form.name,
      gender: form.gender,
      age: form.age,
      birth: form.birth,
      zodiac: form.zodiac,
      constellation: form.constellation,
      job: form.job,
      additional: form.additional,
      contact: form.contact,
      position: form.position,
      goal: form.goal,
    },
    interact: {
      playSound: form.playSound,
      QnA: form.qna,
      perception: { follow: form.perceptionFollow },
    },
    memory: {
      isolate_by_user: form.memoryIsolateByUser,
      use_bionic_memory: false,
    },
    items: [],
  };
}

async function loadConfig() {
  loading.value = true;
  try {
    const data = await getData();
    hydrate(data.config);
    appStore.voiceList = (data.voice_list || []).map((voice) => ({
      value: voice.value || voice.id || '',
      label: voice.label || voice.name || '',
    }));
  } finally {
    loading.value = false;
  }
}

async function saveConfig() {
  await submitConfig(toConfig());
  ElMessage.success('配置已保存');
}

async function toggleLive() {
  if (appStore.liveState === 1) {
    await appStore.stopLive();
  } else {
    await appStore.startLive();
  }
}

async function handleClearMemory() {
  await ElMessageBox.confirm('清除记忆会删除 Fay 的对话记忆，需重启后完全生效。确认继续？', '清除记忆', { type: 'warning' });
  const result = await clearMemory();
  if (result.success) {
    ElMessage.success(result.message);
  } else {
    ElMessage.error(result.message);
  }
}

async function clonePersonality() {
  if (appStore.liveState !== 1) {
    ElMessage.warning('请先开启 Fay 服务');
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

onMounted(loadConfig);
</script>

<template>
  <section class="panel settings-panel" v-loading="loading">
    <div class="panel-header">
      <div>
        <h2>人设配置</h2>
        <p>调整 Fay 的基础人格、语音、唤醒和记忆策略。</p>
      </div>
      <div class="header-actions">
        <el-button :icon="Save" type="primary" :disabled="!appStore.configEditable" @click="saveConfig">保存配置</el-button>
        <el-button :icon="appStore.liveState === 1 ? Square : Play" @click="toggleLive">{{ liveButtonText }}</el-button>
      </div>
    </div>

    <el-form label-position="top" class="settings-form" :disabled="!appStore.configEditable">
      <div class="form-section">
        <h3>基础人设</h3>
        <div class="form-grid">
          <el-form-item label="姓名"><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="性别"><el-input v-model="form.gender" /></el-form-item>
          <el-form-item label="年龄"><el-input v-model="form.age" /></el-form-item>
          <el-form-item label="出生地"><el-input v-model="form.birth" /></el-form-item>
          <el-form-item label="生肖"><el-input v-model="form.zodiac" /></el-form-item>
          <el-form-item label="星座"><el-input v-model="form.constellation" /></el-form-item>
          <el-form-item label="定位">
            <el-select v-model="form.position">
              <el-option v-for="item in positionOptions" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>
          <el-form-item label="目标">
            <el-select v-model="form.goal">
              <el-option v-for="item in goalOptions" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>
          <el-form-item label="职业"><el-input v-model="form.job" /></el-form-item>
          <el-form-item label="联系方式"><el-input v-model="form.contact" /></el-form-item>
        </div>
        <el-form-item label="补充">
          <el-input v-model="form.additional" type="textarea" :autosize="{ minRows: 4, maxRows: 8 }" />
        </el-form-item>
      </div>

      <div class="form-section">
        <h3>声音与交互</h3>
        <div class="form-grid">
          <el-form-item label="声音选择">
            <el-select v-model="form.voice" filterable>
              <el-option v-for="voice in appStore.voiceList" :key="voice.value" :label="voice.label" :value="voice.value" />
            </el-select>
          </el-form-item>
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

    <div class="danger-zone">
      <el-button :icon="Trash2" @click="handleClearMemory">清除记忆</el-button>
      <el-button :icon="WandSparkles" @click="clonePersonality">克隆人格</el-button>
    </div>
  </section>
</template>
