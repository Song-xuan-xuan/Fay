import { onBeforeUnmount, onMounted, type Ref } from 'vue';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

function resolveHomeScroller(root: HTMLElement) {
  const candidate = root.closest<HTMLElement>('.stage-content');
  if (!candidate) return undefined;
  const overflowY = window.getComputedStyle(candidate).overflowY;
  const canScroll = ['auto', 'scroll'].includes(overflowY) && candidate.scrollHeight > candidate.clientHeight;
  return canScroll ? candidate : undefined;
}

function setupHeroMotion() {
  const elements = gsap.utils.toArray<HTMLElement>('[data-home-hero]');
  gsap.from(elements, {
    opacity: 0,
    y: 34,
    duration: 1.05,
    stagger: 0.11,
    ease: 'power3.out',
    clearProps: 'opacity,transform',
  });
}

function setupRevealMotion(scroller?: HTMLElement) {
  gsap.utils.toArray<HTMLElement>('[data-home-reveal]').forEach((element, index) => {
    const heading = element.classList.contains('home-section-heading');
    gsap.from(element, {
      opacity: 0,
      y: heading ? 30 : 46,
      duration: heading ? 0.82 : 0.94,
      delay: (index % 3) * 0.05,
      ease: 'power3.out',
      clearProps: 'opacity,transform',
      scrollTrigger: { trigger: element, scroller, start: 'top 84%', once: true },
    });
  });
}

function setupInsightCounters(scroller?: HTMLElement) {
  gsap.utils.toArray<HTMLElement>('[data-home-count]').forEach((element) => {
    const rawValue = element.dataset.homeCount || '0';
    const target = Number(rawValue);
    const decimals = rawValue.includes('.') ? rawValue.split('.')[1].length : 0;
    if (!Number.isFinite(target)) return;
    const counter = { value: 0 };
    gsap.to(counter, {
      value: target,
      duration: 1.45,
      ease: 'power2.out',
      onUpdate: () => { element.textContent = counter.value.toFixed(decimals); },
      onComplete: () => { element.textContent = rawValue; },
      scrollTrigger: { trigger: element, scroller, start: 'top 88%', once: true },
    });
  });
}

function setupParallax(scroller?: HTMLElement) {
  gsap.utils.toArray<HTMLElement>('[data-home-parallax]').forEach((element) => {
    gsap.to(element, {
      yPercent: -10,
      ease: 'none',
      scrollTrigger: { trigger: element, scroller, scrub: 1, start: 'top bottom', end: 'bottom top' },
    });
  });
}

export function useHomeMotion(root: Ref<HTMLElement | null>) {
  let context: gsap.Context | undefined;

  onMounted(() => {
    if (!root.value || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    const scroller = resolveHomeScroller(root.value);
    gsap.registerPlugin(ScrollTrigger);
    context = gsap.context(() => {
      setupHeroMotion();
      setupRevealMotion(scroller);
      setupInsightCounters(scroller);
      setupParallax(scroller);
    }, root.value);
  });

  onBeforeUnmount(() => context?.revert());
}
