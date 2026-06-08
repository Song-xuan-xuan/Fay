<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { Mic, MicOff, Power, Send, Volume2, VolumeX, Image as ImageIcon, X } from '@lucide/vue';
import { ElMessage } from 'element-plus';

defineProps<{
  modelValue: string;
  canSend: boolean;
  liveState: number;
  micEnabled: boolean;
  speakerEnabled: boolean;
  showManagementControls: boolean;
}>();

const emit = defineEmits<{
  (event: 'update:modelValue', value: string): void;
  (event: 'submit'): void;
  (event: 'toggle-mic'): void;
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
    <!-- 图片预览区域 -->
    <div v-if="imagePreviews.length > 0" class="image-previews">
      <div v-for="(preview, index) in imagePreviews" :key="index" class="image-preview-item">
        <img :src="preview" alt="预览图片" />
        <button class="remove-image-btn" @click="removeImage(index)">
          <X :size="16" />
        </button>
      </div>
    </div>

    <el-input
      :model-value="modelValue"
      type="textarea"
      :autosize="{ minRows: 1, maxRows: 4 }"
      :placeholder="imagePreviews.length > 0 ? `已添加 ${imagePreviews.length} 张图片，可继续粘贴或输入文字` : '输入消息，Enter 发送（支持粘贴图片）'"
      @update:model-value="emit('update:modelValue', $event)"
      @keydown.enter.exact.prevent="emit('submit')"
    />
    <el-button type="primary" :icon="Send" :disabled="!canSend && imagePreviews.length === 0" @click="emit('submit')">发送</el-button>
    <div v-if="showManagementControls" class="composer-controls">
      <el-button
        :icon="micEnabled ? Mic : MicOff"
        :aria-label="micEnabled ? '关闭麦克风' : '开启麦克风'"
        @click="emit('toggle-mic')"
      />
      <el-button
        v-if="liveState === 1"
        :icon="speakerEnabled ? Volume2 : VolumeX"
        :aria-label="speakerEnabled ? '关闭扬声器' : '开启扬声器'"
        @click="emit('toggle-speaker')"
      />
      <el-button v-else :icon="Power" aria-label="启动 Fay 服务" @click="emit('start-live')" />
    </div>
  </footer>
</template>

<style scoped>
.composer {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  align-items: end;
  gap: 8px;
}

.composer-controls {
  display: flex;
  gap: 8px;
}

.composer-controls :deep(.el-button) {
  min-width: 44px;
  min-height: 40px;
  margin-left: 0;
}

/* 图片预览区域 */
.image-previews {
  grid-column: 1 / -1;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  padding: 8px;
  background: #f5f5f5;
  border-radius: 4px;
}

.image-preview-item {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid #ddd;
}

.image-preview-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.remove-image-btn {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  padding: 0;
}

.remove-image-btn:hover {
  background: rgba(0, 0, 0, 0.8);
}
</style>
