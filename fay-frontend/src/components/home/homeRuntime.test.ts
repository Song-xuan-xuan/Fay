import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import homeSource from '../../views/Home.vue?raw';
import heroSource from './HomeHero.vue?raw';
import humanSource from './PublicDigitalHuman.vue?raw';
import ragSource from './RagStory.vue?raw';
import routeSource from './RouteStory.vue?raw';
import particleSource from './ParticleCanvas.vue?raw';
import insightSource from './InsightStory.vue?raw';
import motionSource from '../../composables/useHomeMotion.ts?raw';
import layoutSource from '../../layouts/AppLayout.vue?raw';
const homeStyles = readFileSync(fileURLToPath(new URL('../../styles/home.css', import.meta.url)), 'utf8');

describe('homepage runtime fallbacks', () => {
  it('does not mount standalone navigation or ambient audio inside the application shell', () => {
    expect(homeSource).not.toContain('HOME_ASSETS.ambientAudioUrl');
    expect(homeSource).not.toContain('toggleSound');
    expect(homeSource).not.toContain('<audio');
  });

  it('probes the Live2D renderer before mounting its iframe', () => {
    expect(humanSource).toContain("fetch(props.human.render_url, { mode: 'no-cors' })");
    expect(humanSource).toContain('renderAvailable.value = true');
  });

  it('renders knowledge examples continuously instead of switching tabs', () => {
    expect(ragSource).toMatch(/v-for="[^\"]+ in HOME_RAG_QUESTIONS"/);
    expect(ragSource).not.toContain('role="tablist"');
    expect(ragSource).not.toContain('const active');
  });

  it('renders all recommended routes continuously instead of switching tabs', () => {
    expect(routeSource).toMatch(/v-for="[^\"]+ in HOME_ROUTES"/);
    expect(routeSource).not.toContain('role="tablist"');
    expect(routeSource).not.toContain('const active');
  });

  it('inherits the application shell background instead of mounting a standalone nav and backdrop', () => {
    expect(homeSource).not.toContain('HomeNav');
    expect(homeSource).not.toContain('HOME_ASSETS.backgroundUrl');
    expect(homeStyles).not.toContain('position: fixed; inset: 0; z-index: 0');
  });

  it('binds reveal animations to the actual homepage scroll container', () => {
    expect(motionSource).toContain("closest<HTMLElement>('.stage-content')");
    expect(motionSource).toMatch(/scrollTrigger:\s*\{[^}]*scroller/s);
  });

  it('renders the public digital human in an independent homepage stage', () => {
    expect(homeSource).toContain('class="home-human-stage"');
    expect(homeSource).toContain('<PublicDigitalHuman');
    expect(heroSource).not.toContain('PublicDigitalHuman');
    expect(heroSource).not.toContain('data-home-parallax');
  });

  it('keeps the public digital human data type distinct from the Vue component', () => {
    expect(homeSource).toContain('type PublicDigitalHuman as PublicDigitalHumanData');
    expect(homeSource).toContain('ref<PublicDigitalHumanData>');
  });

  it('hides the reusable digital human status only on the homepage', () => {
    expect(humanSource).toContain('showStatus?: boolean');
    expect(humanSource).toContain('showStatus: true');
    expect(humanSource).toContain('v-if="showStatus"');
    expect(homeSource).toContain(':show-status="false"');
  });

  it('uses a lighter route-specific background gradient on the homepage', () => {
    expect(layoutSource).toContain('isHomeRoute.value');
    expect(layoutSource).toContain('homeStageGradient');
    expect(layoutSource).toContain('defaultStageGradient');
  });

  it('renders layered particles with bounded neighbor connections', () => {
    expect(particleSource).toContain('MAX_CONNECTION_DISTANCE');
    expect(particleSource).toContain('drawConnections');
    expect(particleSource).toContain('depth:');
    expect(particleSource).toContain('document.visibilityState');
    expect(particleSource).toContain('motionAllowed && document.visibilityState');
    expect(particleSource).not.toContain("addEventListener('scroll'");
  });

  it('stages the hero entrance and counts insight values once in view', () => {
    expect(heroSource).toContain('data-home-hero');
    expect(insightSource).toContain('data-home-count');
    expect(motionSource).toContain("'[data-home-hero]'");
    expect(motionSource).toContain("'[data-home-count]'");
    expect(motionSource).toContain('stagger:');
  });
});
