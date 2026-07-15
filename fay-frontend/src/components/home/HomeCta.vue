<script setup lang="ts">
import { ArrowRight, LogIn } from '@lucide/vue';
</script>

<template>
  <section id="cta" class="home-section home-cta">
    <div data-home-reveal>
      <p class="home-kicker">YOUR JOURNEY STARTS HERE</p>
      <h2>下一段旅程，<br>从一句话开始。</h2>
      <p>现在，和境语 AI 一起探索灵山。</p>
      <div class="home-actions">
        <RouterLink class="home-button home-button-primary" to="/login"><LogIn :size="18" /> 登录系统</RouterLink>
        <RouterLink class="home-button home-button-ghost" to="/app/chat">进入工作台 <ArrowRight :size="18" /></RouterLink>
      </div>
    </div>
    <footer>境语 AI · 景区数字人知识服务平台</footer>
  </section>
</template>
