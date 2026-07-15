<script setup lang="ts">
import { Clock3, MapPin } from '@lucide/vue';
import { HOME_ROUTES } from '../../config/homeContent';
</script>

<template>
  <section id="route" class="home-section home-story home-route-story">
    <div class="home-section-heading" data-home-reveal>
      <p class="home-index">03 / ROUTE INTELLIGENCE</p>
      <h2>把时间，变成一条刚好的路线</h2>
      <p>不同时间，不同玩法。</p>
    </div>
    <div class="route-list">
      <article v-for="(route, routeIndex) in HOME_ROUTES" :key="route.name" class="route-workspace" data-home-reveal>
        <header class="route-summary">
          <div>
            <span class="route-index">0{{ routeIndex + 1 }}</span>
            <h3>{{ route.name }}</h3>
          </div>
          <div class="route-duration"><Clock3 :size="18" aria-hidden="true" /> {{ route.duration }}</div>
          <p>{{ route.note }}</p>
        </header>
        <ol class="route-stops">
          <li v-for="(stop, index) in route.stops" :key="`${route.name}-${stop}`">
            <i>{{ String(index + 1).padStart(2, '0') }}</i>
            <MapPin :size="17" aria-hidden="true" />
            <span>{{ stop }}</span>
          </li>
        </ol>
      </article>
    </div>
  </section>
</template>
