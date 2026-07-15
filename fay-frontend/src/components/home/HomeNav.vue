<script setup lang="ts">
import { Volume2, VolumeX } from '@lucide/vue';
import { HOME_SECTIONS } from '../../config/homeContent';

defineProps<{ muted: boolean }>();
defineEmits<{ toggleSound: [] }>();
</script>

<template>
  <header class="home-nav">
    <a class="home-brand" href="#hero" aria-label="境语 AI 首页">境语 <span>AI</span></a>
    <nav aria-label="首页章节">
      <a v-for="section in HOME_SECTIONS.slice(1, 6)" :key="section.id" :href="`#${section.id}`">
        {{ section.label }}
      </a>
    </nav>
    <div class="home-nav-actions">
      <button class="home-icon-button" type="button" :aria-label="muted ? '开启环境音' : '关闭环境音'" @click="$emit('toggleSound')">
        <VolumeX v-if="muted" :size="19" />
        <Volume2 v-else :size="19" />
      </button>
      <RouterLink class="home-nav-login" to="/login">登录</RouterLink>
    </div>
  </header>
</template>
