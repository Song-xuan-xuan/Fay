import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';

const componentsCss = readFileSync(new URL('../src/styles/components.css', import.meta.url), 'utf-8');

describe('immersive management panel styles', () => {
  it('wraps high-density pages in large glass panels over the stage background', () => {
    expect(componentsCss).toContain('.stage-content > .panel');
    expect(componentsCss).toContain('.stage-content > .dashboard-shell');
    expect(componentsCss).toContain('.stage-content > .recommendation-page');
    expect(componentsCss).toContain('border-radius: 28px');
    expect(componentsCss).toContain('backdrop-filter: blur(26px) saturate(165%)');
  });

  it('keeps the digital human library outer surface transparent', () => {
    expect(componentsCss).toContain('.stage-content > .live2d-page {');
    expect(componentsCss).toContain('background: transparent;');
    expect(componentsCss).toContain('box-shadow: none;');
    expect(componentsCss).toContain('border: 0;');
  });

  it('keeps tall management panels at their content height inside the scrolling stage', () => {
    const sharedPanelBlock = componentsCss.match(
      /\.stage-content > \.panel,[\s\S]*?\.stage-content > \.settings-panel\s*\{([\s\S]*?)\n\}/,
    )?.[1] ?? '';

    expect(sharedPanelBlock).toContain('flex: 0 0 auto;');
  });
});
