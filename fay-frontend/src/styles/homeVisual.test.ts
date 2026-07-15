import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const homeStyles = readFileSync(fileURLToPath(new URL('./home.css', import.meta.url)), 'utf8');
const homeMotionStyles = readFileSync(fileURLToPath(new URL('./home-motion.css', import.meta.url)), 'utf8');
const mainStyles = readFileSync(fileURLToPath(new URL('./main.css', import.meta.url)), 'utf8');
const capabilityNetworkSource = readFileSync(fileURLToPath(new URL('../components/home/CapabilityNetwork.vue', import.meta.url)), 'utf8');

function getDeclarations(selector: string) {
  const rulePattern = /([^{}]+)\{([^{}]*)\}/g;

  return [...homeStyles.matchAll(rulePattern)]
    .filter((match) => match[1].split(',').some((entry) => entry.trim() === selector))
    .map((match) => match[2])
    .join('\n');
}

describe('homepage visual system', () => {
  it('uses the blue-white rounded visual language', () => {
    expect(homeStyles).toContain('--home-blue-600');
    expect(homeStyles).toContain('--home-radius: 8px');
    expect(homeStyles).toContain('background: #fff');
  });

  it('keeps the page in a continuous scroll flow', () => {
    expect(homeStyles).not.toContain('scroll-snap-type');
    expect(homeStyles).not.toContain('min-height: 100svh');
    expect(homeStyles).toMatch(/\.public-home\s*\{[^}]*flex:\s*0 0 auto;/s);
  });

  it('keeps the ambient canvas viewport-sized instead of allocating the full page height', () => {
    const particles = getDeclarations('.home-particles');

    expect(particles).toContain('position: fixed;');
    expect(particles).toContain('height: 100vh;');
    expect(particles).toContain('left: 104px;');
    expect(particles).toContain('right: clamp(340px, 27vw, 540px);');
    expect(particles).toContain('width: calc(100vw - 104px - clamp(340px, 27vw, 540px));');
    expect(homeStyles).toMatch(/@media \(max-width:\s*768px\)[\s\S]*\.home-particles\s*\{[^}]*width:\s*100vw;/);
  });

  it('fixes the homepage digital human in the desktop right-side stage', () => {
    expect(homeStyles).toMatch(/\.home-human-stage\s*\{[^}]*position:\s*fixed;[^}]*right:\s*0;/s);
    expect(homeStyles).toMatch(/@media \(max-width:\s*1180px\)[\s\S]*\.home-human-stage\s*\{[^}]*position:\s*relative;/s);
  });

  it('uses an open page canvas and a single-column hero instead of a large card', () => {
    const page = getDeclarations('.public-home');
    const hero = getDeclarations('.home-hero');

    expect(page).not.toContain('border:');
    expect(page).not.toContain('border-radius:');
    expect(page).not.toContain('backdrop-filter:');
    expect(page).not.toContain('background:');
    expect(homeStyles).not.toContain('.public-home::before');
    expect(homeStyles).not.toContain('.public-home::after');
    expect(hero).not.toContain('grid-template-columns:');
  });

  it('keeps the digital human and content sections free of card surfaces', () => {
    const openSelectors = [
      '.public-human',
      '.guide-console',
      '.rag-example',
      '.route-workspace',
      '.network-node',
      '.insight-grid',
    ];

    openSelectors.forEach((selector) => {
      const declarations = getDeclarations(selector);
      const backgrounds = [...declarations.matchAll(/background:\s*([^;]+);/g)].map((match) => match[1].trim());
      expect(declarations, selector).not.toContain('box-shadow:');
      expect(backgrounds.every((value) => value === 'transparent'), selector).toBe(true);
      expect(declarations, selector).not.toContain('border-radius:');
    });
  });

  it('resets homepage buttons and scopes the capability connector svg', () => {
    expect(getDeclarations('.public-human')).toContain('background: transparent;');
    expect(getDeclarations('.network-node')).toContain('background: transparent;');
    expect(getDeclarations('.network-node')).toContain('appearance: none;');
    expect(homeStyles).toContain('.capability-network > svg');
    expect(homeStyles).not.toContain('.capability-network svg {');
  });

  it('keeps editorial copy readable over switchable backgrounds', () => {
    const backdrop = getDeclarations('.immersive-shell.is-home-route .stage-background::after');
    const heading = getDeclarations('.home-section-heading');

    expect(backdrop).toContain('linear-gradient');
    expect(heading).toContain('width: 100%;');
  });

  it('keeps homepage copy legible over detailed backgrounds', () => {
    expect(homeStyles).toContain('--home-muted: #36536f;');

    const backdrop = getDeclarations('.immersive-shell.is-home-route .stage-background::after');
    expect(backdrop).toContain('rgba(230,245,255,.68) 54%');
    expect(backdrop).toContain('rgba(229,244,255,.42) 72%');
  });

  it('reserves enough space for the larger RAG typography', () => {
    const step = getDeclarations('.rag-flow-step');
    const label = getDeclarations('.rag-flow-step span');
    const question = getDeclarations('.rag-flow-step strong');
    const list = getDeclarations('.rag-flow-step ul');
    const answer = getDeclarations('.rag-answer p');

    expect(step).toContain('min-height: 220px;');
    expect(label).toContain('font-size: 13px;');
    expect(question).toContain('font-size: 18px;');
    expect(list).toContain('font-size: 14px;');
    expect(answer).toContain('font-size: 15px;');
  });

  it('raises the smallest supporting copy without changing heading scale', () => {
    const sectionCopy = getDeclarations('.home-section-heading > p:last-child');
    const routeCopy = getDeclarations('.route-summary p');
    const routeStop = getDeclarations('.route-stops span');
    const networkCopy = getDeclarations('.network-node span');

    expect(sectionCopy).toContain('font-size: 17px;');
    expect(sectionCopy).toContain('font-weight: 500;');
    expect(routeCopy).toContain('font-size: 14px;');
    expect(routeStop).toContain('font-size: 14px;');
    expect(networkCopy).toContain('font-size: 12px;');
  });

  it('provides a reduced-motion fallback', () => {
    expect(homeStyles).toContain('prefers-reduced-motion: reduce');
  });

  it('loads a dedicated cinematic motion layer', () => {
    expect(mainStyles).toContain("@import './home-motion.css';");
    expect(homeMotionStyles).toContain('@keyframes home-background-breathe');
    expect(homeMotionStyles).toContain('.immersive-shell.is-home-route .stage-background');
  });

  it('adds restrained motion accents to actions, routes, and the capability network', () => {
    expect(homeMotionStyles).toContain('.home-button::after');
    expect(homeMotionStyles).toContain('@keyframes home-button-sweep');
    expect(homeMotionStyles).toContain('.route-stops li::after');
    expect(homeMotionStyles).toContain('@keyframes home-route-flow');
    expect(homeMotionStyles).toContain('.capability-network > svg line');
    expect(homeMotionStyles).toContain('@keyframes home-network-flow');
    expect(homeMotionStyles).toContain('.network-core::before');
  });

  it('gives the capability network a stronger central focus', () => {
    const core = getDeclarations('.network-core');
    const node = getDeclarations('.network-node');

    expect(core).toContain('width: 210px;');
    expect(core).toContain('height: 210px;');
    expect(homeStyles).toContain('.network-core::after');
    expect(node).toContain('position: absolute;');
    expect(homeStyles).toContain('.network-node::before');
  });

  it('adds animated signal points while preserving reduced-motion behavior', () => {
    expect(capabilityNetworkSource).toContain('class="network-signal"');
    expect(homeMotionStyles).toContain('.network-signal');
    expect(homeMotionStyles).toContain('@keyframes home-network-signal');
    expect(homeMotionStyles).toMatch(/@media \(prefers-reduced-motion: reduce\)[\s\S]*\.network-signal/);
  });

  it('keeps animated insight numbers at the original metric scale', () => {
    const number = getDeclarations('.insight-grid .insight-value-number');

    expect(number).toContain('color: inherit;');
    expect(number).toContain('font-size: inherit;');
  });

  it('turns off every continuous cinematic effect for reduced motion', () => {
    expect(homeMotionStyles).toMatch(/@media \(prefers-reduced-motion: reduce\)[\s\S]*animation:\s*none\s*!important;/);
  });
});
