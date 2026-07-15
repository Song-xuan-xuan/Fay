<script setup lang="ts">
import { HOME_INSIGHTS } from '../../config/homeContent';
</script>

<template>
  <section id="insights" class="home-section home-story home-insight-story">
    <div class="home-section-heading" data-home-reveal>
      <p class="home-index">05 / REAL DATA</p>
      <h2>从每一次游览，看见真实需求</h2>
      <p>用数据理解游客，用洞察优化服务。</p>
    </div>
    <div class="insight-grid" data-home-reveal>
      <article v-for="item in HOME_INSIGHTS" :key="item.label">
        <span>{{ item.label }}</span>
        <strong><span class="insight-value-number" :data-home-count="item.value">{{ item.value }}</span><small>{{ item.unit }}</small></strong>
      </article>
    </div>
  </section>
</template>
