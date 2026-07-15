<script setup lang="ts">
import { onMounted, ref } from 'vue';
import { getPublicDigitalHuman, type PublicDigitalHuman as PublicDigitalHumanData } from '../api/publicHomepage';
import CapabilityNetwork from '../components/home/CapabilityNetwork.vue';
import DigitalHumanStory from '../components/home/DigitalHumanStory.vue';
import HomeCta from '../components/home/HomeCta.vue';
import HomeHero from '../components/home/HomeHero.vue';
import InsightStory from '../components/home/InsightStory.vue';
import ParticleCanvas from '../components/home/ParticleCanvas.vue';
import PublicDigitalHuman from '../components/home/PublicDigitalHuman.vue';
import RagStory from '../components/home/RagStory.vue';
import RouteStory from '../components/home/RouteStory.vue';
import { HOME_ASSETS } from '../config/homeContent';
import { useHomeMotion } from '../composables/useHomeMotion';

const root = ref<HTMLElement | null>(null);
const greeting = ref('');
const human = ref<PublicDigitalHumanData>({
  name: '境语导览员', type: 'image', render_url: '', cover_url: HOME_ASSETS.defaultHumanCover,
});

useHomeMotion(root);

function greet() {
  greeting.value = '你好，我是境语导览员。想听灵山故事，还是规划一条游览路线？';
  window.setTimeout(() => { greeting.value = ''; }, 5200);
}

async function loadHuman() {
  try {
    const response = await getPublicDigitalHuman();
    if (response.digital_human) human.value = response.digital_human;
  } catch {
    // 静态数字人已作为无需后端的回退状态。
  }
}

onMounted(loadHuman);
</script>

<template>
  <main ref="root" class="public-home">
    <ParticleCanvas />
    <HomeHero />
    <aside class="home-human-stage" aria-label="首页数字人展示">
      <div class="home-human-stage-body">
        <PublicDigitalHuman :human="human" :show-status="false" @greet="greet" />
        <p v-if="greeting" class="home-greeting">{{ greeting }}</p>
      </div>
    </aside>
    <DigitalHumanStory />
    <RagStory />
    <RouteStory />
    <CapabilityNetwork />
    <InsightStory />
    <HomeCta />
  </main>
</template>
