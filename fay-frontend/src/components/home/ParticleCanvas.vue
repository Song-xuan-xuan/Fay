<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue';

interface Particle {
  x: number;
  y: number;
  radius: number;
  speed: number;
  alpha: number;
  depth: number;
  phase: number;
  warm: boolean;
}

const MOBILE_BREAKPOINT = 768;
const MOBILE_PARTICLE_COUNT = 26;
const DESKTOP_PARTICLE_COUNT = 64;
const MAX_CONNECTION_DISTANCE = 142;
const MAX_PIXEL_RATIO = 2;
const FULL_CIRCLE = Math.PI * 2;

const canvas = ref<HTMLCanvasElement | null>(null);
let frame = 0;
let particles: Particle[] = [];
let pixelRatio = 1;
let motionAllowed = false;

function createParticles(width: number, height: number, mobile: boolean) {
  const count = mobile ? MOBILE_PARTICLE_COUNT : DESKTOP_PARTICLE_COUNT;
  particles = Array.from({ length: count }, () => ({
    x: Math.random() * width,
    y: Math.random() * height,
    radius: Math.random() * 1.4 + 0.45,
    speed: Math.random() * 0.2 + 0.05,
    alpha: Math.random() * 0.46 + 0.18,
    depth: Math.random() * 0.75 + 0.25,
    phase: Math.random() * FULL_CIRCLE,
    warm: Math.random() > 0.82,
  }));
}

function resize() {
  const target = canvas.value;
  if (!target) return;
  pixelRatio = Math.min(window.devicePixelRatio || 1, MAX_PIXEL_RATIO);
  target.width = Math.round(target.clientWidth * pixelRatio);
  target.height = Math.round(target.clientHeight * pixelRatio);
  createParticles(target.width, target.height, target.clientWidth < MOBILE_BREAKPOINT);
  renderScene(false);
}

function drawConnections(context: CanvasRenderingContext2D) {
  const limit = MAX_CONNECTION_DISTANCE * pixelRatio;
  for (let index = 0; index < particles.length; index += 1) {
    const particle = particles[index];
    if (particle.depth < 0.58) continue;
    for (let neighborIndex = index + 1; neighborIndex < particles.length; neighborIndex += 1) {
      const neighbor = particles[neighborIndex];
      if (neighbor.depth < 0.58) continue;
      const distance = Math.hypot(particle.x - neighbor.x, particle.y - neighbor.y);
      if (distance > limit) continue;
      const alpha = (1 - distance / limit) * 0.12 * Math.min(particle.depth, neighbor.depth);
      context.beginPath();
      context.strokeStyle = `rgba(76, 167, 226, ${alpha})`;
      context.lineWidth = pixelRatio * 0.7;
      context.moveTo(particle.x, particle.y);
      context.lineTo(neighbor.x, neighbor.y);
      context.stroke();
    }
  }
}

function drawParticles(context: CanvasRenderingContext2D, target: HTMLCanvasElement, advance: boolean) {
  particles.forEach((particle) => {
    if (advance) {
      particle.phase += 0.006;
      particle.x += Math.sin(particle.phase) * 0.08 * particle.depth;
      particle.y -= particle.speed * particle.depth;
    }
    if (particle.y < -4) particle.y = target.height + 4;
    if (particle.x < -4) particle.x = target.width + 4;
    if (particle.x > target.width + 4) particle.x = -4;
    const color = particle.warm ? '232, 188, 98' : '59, 153, 218';
    context.beginPath();
    context.fillStyle = `rgba(${color}, ${particle.alpha * particle.depth})`;
    context.arc(particle.x, particle.y, particle.radius * particle.depth * pixelRatio, 0, FULL_CIRCLE);
    context.fill();
  });
}

function renderScene(advance: boolean) {
  const target = canvas.value;
  const context = target?.getContext('2d');
  if (!target || !context) return;
  context.clearRect(0, 0, target.width, target.height);
  if (target.clientWidth >= MOBILE_BREAKPOINT) drawConnections(context);
  drawParticles(context, target, advance);
}

function tick() {
  renderScene(true);
  frame = requestAnimationFrame(tick);
}

function startAnimation() {
  if (frame || document.visibilityState !== 'visible') return;
  frame = requestAnimationFrame(tick);
}

function stopAnimation() {
  cancelAnimationFrame(frame);
  frame = 0;
}

function handleVisibility() {
  if (motionAllowed && document.visibilityState === 'visible') startAnimation();
  else stopAnimation();
}

onMounted(() => {
  resize();
  window.addEventListener('resize', resize);
  document.addEventListener('visibilitychange', handleVisibility);
  motionAllowed = !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (motionAllowed) startAnimation();
});

onBeforeUnmount(() => {
  stopAnimation();
  window.removeEventListener('resize', resize);
  document.removeEventListener('visibilitychange', handleVisibility);
});
</script>

<template><canvas ref="canvas" class="home-particles" aria-hidden="true" /></template>
