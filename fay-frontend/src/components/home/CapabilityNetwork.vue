<script setup lang="ts">
import { BrainCircuit } from '@lucide/vue';
import { HOME_CAPABILITIES } from '../../config/homeContent';

const NETWORK_LINKS = [
  { x: 130, y: 90 },
  { x: 670, y: 90 },
  { x: 700, y: 350 },
  { x: 400, y: 450 },
  { x: 100, y: 350 },
];
</script>

<template>
  <section id="network" class="home-section home-story home-network-story">
    <div class="home-section-heading" data-home-reveal>
      <p class="home-index">04 / CAPABILITY NETWORK</p>
      <h2>一个数字人，连接整个景区</h2>
      <p>从听见需求，到给出答案。</p>
    </div>
    <div class="capability-network" data-home-reveal>
      <div class="network-core"><BrainCircuit :size="34" /><strong>境语 AI</strong><span>DIGITAL HUMAN</span></div>
      <button v-for="(item, index) in HOME_CAPABILITIES" :key="item.key" type="button" :class="`network-node node-${index + 1}`">
        <small>{{ item.key }}</small><strong>{{ item.label }}</strong><span>{{ item.detail }}</span>
      </button>
      <svg viewBox="0 0 800 500" aria-hidden="true">
        <g>
          <line v-for="(link, index) in NETWORK_LINKS" :key="`link-${index}`" x1="400" y1="250" :x2="link.x" :y2="link.y" />
          <circle v-for="(link, index) in NETWORK_LINKS" :key="`signal-${index}`" class="network-signal" cx="400" cy="250" r="3">
            <animate attributeName="cx" :values="`400;${link.x};400`" :begin="`${index * 0.7}s`" dur="4.8s" repeatCount="indefinite" />
            <animate attributeName="cy" :values="`250;${link.y};250`" :begin="`${index * 0.7}s`" dur="4.8s" repeatCount="indefinite" />
          </circle>
        </g>
      </svg>
    </div>
  </section>
</template>
