<script setup lang="ts">
import { ref } from 'vue';
import { ElMessage } from 'element-plus';
import { ExternalLink, Play, RefreshCw, Square } from '@lucide/vue';
import { liveApi } from '../api/live';
import { useAppStore } from '../stores/app';
import { useLive2dStore } from '../stores/live2d';
import { detectWebglSupport } from '../utils/webgl';

const appStore = useAppStore();
const live2d = useLive2dStore();
const iframeRef = ref<HTMLIFrameElement | null>(null);
const webglSupport = ref(detectWebglSupport());

function reloadFrame() {
  webglSupport.value = detectWebglSupport();
  if (!webglSupport.value.supported) {
    ElMessage.warning(webglSupport.value.message);
  }
  if (iframeRef.value) {
    iframeRef.value.src = live2d.iframeUrl;
  }
}

function sendCommand(command: string) {
  iframeRef.value?.contentWindow?.postMessage({ source: 'fay-console', command }, '*');
  live2d.rememberCommand(command);
  ElMessage.success(`已发送 ${command}`);
}

async function toggleLive() {
  if (appStore.liveState === 1) {
    await liveApi.stopLive();
    appStore.liveState = 0;
  } else {
    await liveApi.startLive();
    appStore.liveState = 1;
  }
}
</script>

<template>
  <section class="live2d-page">
    <div class="panel live2d-toolbar">
      <div>
        <h2>Live2D 数字人</h2>
        <p>通过 iframe 嵌入独立 Live2D 前端，保持 Fay 管理台和模型渲染工程解耦。</p>
      </div>
      <div class="toolbar-actions">
        <el-input v-model="live2d.iframeUrl" aria-label="Live2D 地址" />
        <el-button :icon="RefreshCw" @click="reloadFrame">刷新</el-button>
        <el-button :icon="ExternalLink" tag="a" :href="live2d.iframeUrl" target="_blank">打开</el-button>
        <el-button :icon="appStore.liveState === 1 ? Square : Play" type="primary" @click="toggleLive">
          {{ appStore.liveState === 1 ? '关闭 Fay' : '开启 Fay' }}
        </el-button>
      </div>
    </div>

    <div class="live2d-shell">
      <div class="live2d-stage">
        <div v-if="!webglSupport.supported" class="live2d-diagnostic" role="status">
          <strong>WebGL 预检未通过</strong>
          <span>{{ webglSupport.message }}</span>
          <span>已继续加载 Live2D 页面，请以实际画面为准。</span>
        </div>
        <iframe
          ref="iframeRef"
          :src="live2d.iframeUrl"
          title="Live2D 数字人"
          sandbox="allow-scripts allow-same-origin"
        />
      </div>
      <aside class="panel live2d-control">
        <h3>控制面板</h3>
        <button type="button" @click="sendCommand('expression:smile')">微笑</button>
        <button type="button" @click="sendCommand('motion:greet')">打招呼</button>
        <button type="button" @click="sendCommand('motion:idle')">待机</button>
        <p>最近指令：{{ live2d.lastCommand || '无' }}</p>
      </aside>
    </div>
  </section>
</template>
