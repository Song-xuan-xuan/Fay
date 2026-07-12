<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { AudioLines, MicOff, Power, Send, Volume2, VolumeX, X } from '@lucide/vue';
import { ElMessage } from 'element-plus';
import { BRAND_SERVICE_NAME } from '../../config/brand';

defineProps<{
  modelValue: string;
  canSend: boolean;
  liveState: number;
  micEnabled: boolean;
  speakerEnabled: boolean;
  showManagementControls: boolean;
  canVoiceInput: boolean;
  voiceRecording: boolean;
  voiceTranscribing: boolean;
}>();

const emit = defineEmits<{
  (event: 'update:modelValue', value: string): void;
  (event: 'submit'): void;
  (event: 'toggle-mic'): void;
  (event: 'toggle-voice-input'): void;
  (event: 'toggle-speaker'): void;
  (event: 'start-live'): void;
  (event: 'images-change', images: File[]): void;
}>();

const textareaRef = ref<HTMLTextAreaElement | null>(null);
const pendingImages = ref<File[]>([]);
const imagePreviews = ref<string[]>([]);

// 处理粘贴事件
function handlePaste(event: ClipboardEvent) {
  const items = event.clipboardData?.items;
  if (!items) return;

  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    if (item.type.indexOf('image') !== -1) {
      event.preventDefault();
      const file = item.getAsFile();
      if (file) {
        addImage(file);
      }
    }
  }
}

// 添加图片
function addImage(file: File) {
  // 限制图片数量
  if (pendingImages.value.length >= 10) {
    ElMessage.warning('最多只能上传10张图片');
    return;
  }

  // 限制文件大小（20MB）
  if (file.size > 20 * 1024 * 1024) {
    ElMessage.warning('图片大小不能超过20MB');
    return;
  }

  // 检查文件类型
  const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp'];
  if (!validTypes.includes(file.type)) {
    ElMessage.warning('只支持 JPG, PNG, GIF, WebP, BMP 格式的图片');
    return;
  }

  pendingImages.value.push(file);

  // 生成预览
  const reader = new FileReader();
  reader.onload = (e) => {
    if (e.target?.result) {
      imagePreviews.value.push(e.target.result as string);
    }
  };
  reader.readAsDataURL(file);

  emit('images-change', pendingImages.value);
}

// 移除图片
function removeImage(index: number) {
  pendingImages.value.splice(index, 1);
  imagePreviews.value.splice(index, 1);
  emit('images-change', pendingImages.value);
}

// 清空图片（发送后调用）
function clearImages() {
  pendingImages.value = [];
  imagePreviews.value = [];
  emit('images-change', []);
}

// 暴露清空方法给父组件
defineExpose({
  clearImages
});

onMounted(() => {
  const textarea = document.querySelector('.composer textarea') as HTMLTextAreaElement;
  if (textarea) {
    textareaRef.value = textarea;
    textarea.addEventListener('paste', handlePaste);
  }
});

onUnmounted(() => {
  if (textareaRef.value) {
    textareaRef.value.removeEventListener('paste', handlePaste);
  }
});
</script>

<template>
  <footer class="composer">
    <div class="composer-shell">
      <div v-if="imagePreviews.length > 0" class="image-previews">
        <div v-for="(preview, index) in imagePreviews" :key="index" class="image-preview-item">
          <img :src="preview" alt="预览图片" />
          <button class="remove-image-btn" aria-label="移除图片" @click="removeImage(index)">
            <X :size="16" />
          </button>
        </div>
      </div>

      <div class="composer-input">
        <el-input
          :model-value="modelValue"
          type="textarea"
          :autosize="{ minRows: 1, maxRows: 4 }"
          :placeholder="imagePreviews.length > 0 ? `已添加 ${imagePreviews.length} 张图片，可继续粘贴或输入文字` : '输入消息，Enter 发送（支持粘贴图片）'"
          @update:model-value="emit('update:modelValue', $event)"
          @keydown.enter.exact.prevent="emit('submit')"
        />
      </div>

      <div class="composer-toolbar">
        <el-button
          class="composer-icon-button voice-input-button"
          :type="voiceRecording ? 'danger' : 'default'"
          :icon="AudioLines"
          circle
          :loading="voiceTranscribing"
          :disabled="voiceTranscribing || (!canVoiceInput && !voiceRecording)"
          :aria-label="voiceRecording ? '停止手动语音输入并发送' : '手动语音发送'"
          title="手动语音发送：停止录音后才识别并发送"
          @click="emit('toggle-voice-input')"
        />
        <el-button
          v-if="showManagementControls"
          class="composer-icon-button realtime-listen-button"
          :class="{ listening: micEnabled }"
          :type="micEnabled ? 'warning' : 'default'"
          :icon="micEnabled ? AudioLines : MicOff"
          circle
          :disabled="!micEnabled && (liveState !== 1 || !canVoiceInput)"
          :aria-label="micEnabled ? '关闭连续语音对话' : '开启连续语音对话'"
          :title="micEnabled ? '连续对话中，点击关闭' : '开启连续对话，无需唤醒词'"
          @click="emit('toggle-mic')"
        />
        <el-button
          v-if="showManagementControls && liveState === 1"
          class="composer-icon-button"
          :icon="speakerEnabled ? Volume2 : VolumeX"
          circle
          :aria-label="speakerEnabled ? '关闭扬声器' : '开启扬声器'"
          :title="speakerEnabled ? '关闭扬声器' : '开启扬声器'"
          @click="emit('toggle-speaker')"
        />
        <el-button
          v-else-if="showManagementControls"
          class="composer-icon-button"
          :icon="Power"
          circle
          :aria-label="`启动 ${BRAND_SERVICE_NAME}`"
          :title="`启动 ${BRAND_SERVICE_NAME}`"
          @click="emit('start-live')"
        />
        <el-button
          class="composer-icon-button send-button"
          type="primary"
          :icon="Send"
          circle
          :disabled="!canSend && imagePreviews.length === 0"
          aria-label="发送消息"
          title="发送消息"
          @click="emit('submit')"
        />
      </div>
    </div>
  </footer>
</template>

<style scoped src="./ChatComposer.css"></style>
