<script setup lang="ts">
import { BookOpen, Search, Sparkles } from '@lucide/vue';
import { HOME_RAG_QUESTIONS } from '../../config/homeContent';
</script>

<template>
  <section id="rag" class="home-section home-story home-rag-story">
    <div class="home-section-heading" data-home-reveal>
      <p class="home-index">02 / RAG KNOWLEDGE</p>
      <h2>有依据的回答，才值得信任</h2>
      <p>从景区知识中寻找答案。</p>
    </div>
    <div class="rag-workspace" data-home-reveal>
      <article v-for="(item, index) in HOME_RAG_QUESTIONS" :key="item.question" class="rag-example" data-home-reveal>
        <div class="rag-example-index">0{{ index + 1 }}</div>
        <div class="rag-flow">
          <div class="rag-flow-step">
            <Search :size="21" aria-hidden="true" />
            <span>游客提问</span>
            <strong>{{ item.question }}</strong>
          </div>
          <div class="rag-flow-step">
            <BookOpen :size="21" aria-hidden="true" />
            <span>检索依据</span>
            <ul>
              <li v-for="reference in item.references" :key="reference">{{ reference }}</li>
            </ul>
          </div>
          <div class="rag-flow-step rag-answer">
            <Sparkles :size="21" aria-hidden="true" />
            <span>生成回答</span>
            <p>{{ item.answer }}</p>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>
