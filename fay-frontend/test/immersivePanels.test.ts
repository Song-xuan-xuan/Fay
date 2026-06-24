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
});
