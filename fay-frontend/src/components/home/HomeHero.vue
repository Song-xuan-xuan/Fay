<script setup lang="ts">
import { ArrowDown, ArrowRight } from '@lucide/vue';
</script>

<template>
  <section id="hero" class="home-section home-hero">
    <div class="home-hero-copy">
      <p class="home-kicker" data-home-hero>JINGYU AI · DIGITAL SCENIC GUIDE</p>
      <h1 data-home-hero>境语 <strong>AI</strong></h1>
      <h2 data-home-hero>景区数字人知识服务平台</h2>
      <p class="home-lead" data-home-hero>让景区会讲述，让服务更懂游客。<br>知识随时可问，路线因人而定。</p>
      <div class="home-actions" data-home-hero>
        <RouterLink class="home-button home-button-primary" to="/login">开始体验 <ArrowRight :size="18" /></RouterLink>
        <a class="home-button home-button-ghost" href="#network">探索系统能力</a>
      </div>
      <a class="home-scroll-cue" href="#guide" data-home-hero><ArrowDown :size="18" /> 向下探索</a>
    </div>
  </section>
</template>
