<script setup lang="ts">
import { AudioLines, MessageCircle, ScanFace } from '@lucide/vue';
</script>

<template>
  <section id="guide" class="home-section home-story home-guide-story">
    <div class="home-section-heading" data-home-reveal>
      <p class="home-index">01 / DIGITAL HUMAN</p>
      <h2>让景区知识，真正开口说话</h2>
      <p>听得懂问题，也说得清风景。</p>
    </div>
    <div class="guide-console" data-home-reveal>
      <div class="guide-wave" aria-hidden="true"><i v-for="n in 22" :key="n" :style="{ height: `${18 + (n % 7) * 7}px` }" /></div>
      <div class="guide-dialogue">
        <p><span>游客</span>半天时间，怎样更好地了解灵山？</p>
        <p class="answer"><span>境语 AI</span>从南门出发，沿中轴线游览。我会为你串联历史、建筑与核心景点。</p>
      </div>
      <div class="guide-states">
        <span><AudioLines :size="18" /> 语音识别</span>
        <span><MessageCircle :size="18" /> 语义理解</span>
        <span><ScanFace :size="18" /> 口型与动作</span>
      </div>
    </div>
  </section>
</template>
