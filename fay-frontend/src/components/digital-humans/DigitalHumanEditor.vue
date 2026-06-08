<script setup lang="ts">
import { ref } from 'vue';
import { ImagePlus } from '@lucide/vue';
import type { DigitalHumanPayload } from '../../types';

defineProps<{
  editing: boolean;
  form: DigitalHumanPayload;
  saving: boolean;
  voiceList: Array<{ value: string; label: string }>;
}>();

const visible = defineModel<boolean>('visible', { required: true });
const tagText = defineModel<string>('tagText', { required: true });
const emit = defineEmits<{ save: []; coverChange: [file: File] }>();
const coverInput = ref<HTMLInputElement | null>(null);

function triggerCoverUpload() {
  coverInput.value?.click();
}

function handleCoverChange(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  input.value = '';
  if (file) {
    emit('coverChange', file);
  }
}
</script>

<template>
  <el-drawer v-model="visible" :title="editing ? '编辑数字人' : '新增数字人'" size="520px">
    <el-form label-position="top" class="digital-human-form">
      <div class="cover-editor">
        <img :src="form.cover_url || '/static/images/Normal.gif'" alt="" />
        <div>
          <el-button :icon="ImagePlus" :disabled="!editing" @click="triggerCoverUpload">上传封面</el-button>
          <p>新增数字人保存后可上传封面。</p>
          <input ref="coverInput" class="visually-hidden-input" type="file" accept="image/*" @change="handleCoverChange" />
        </div>
      </div>
      <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
      <el-form-item label="类型">
        <el-select v-model="form.type">
          <el-option label="Live2D" value="live2d" />
          <el-option label="网页 iframe" value="iframe" />
          <el-option label="图片/GIF" value="image" />
        </el-select>
      </el-form-item>
      <el-form-item label="渲染地址"><el-input v-model="form.render_url" placeholder="http://127.0.0.1:5174" /></el-form-item>
      <el-form-item label="封面地址"><el-input v-model="form.cover_url" /></el-form-item>
      <el-form-item label="声音">
        <el-select v-model="form.voice" filterable>
          <el-option v-for="voice in voiceList" :key="voice.value" :label="voice.label" :value="voice.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="标签"><el-input v-model="tagText" placeholder="销售, 活泼" /></el-form-item>
      <div class="form-grid compact">
        <el-form-item label="性别"><el-input v-model="form.persona!.gender" /></el-form-item>
        <el-form-item label="年龄"><el-input v-model="form.persona!.age" /></el-form-item>
        <el-form-item label="出生地"><el-input v-model="form.persona!.birth" /></el-form-item>
        <el-form-item label="生肖"><el-input v-model="form.persona!.zodiac" /></el-form-item>
        <el-form-item label="星座"><el-input v-model="form.persona!.constellation" /></el-form-item>
        <el-form-item label="职业"><el-input v-model="form.persona!.job" /></el-form-item>
        <el-form-item label="定位"><el-input v-model="form.persona!.position" /></el-form-item>
        <el-form-item label="目标"><el-input v-model="form.persona!.goal" /></el-form-item>
      </div>
      <el-form-item label="联系方式"><el-input v-model="form.persona!.contact" /></el-form-item>
      <el-form-item label="补充人设">
        <el-input v-model="form.persona!.additional" type="textarea" :autosize="{ minRows: 4, maxRows: 8 }" />
      </el-form-item>
    </el-form>
    <template #footer>
      <div class="drawer-footer">
        <el-button @click="visible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="emit('save')">保存</el-button>
      </div>
    </template>
  </el-drawer>
</template>
