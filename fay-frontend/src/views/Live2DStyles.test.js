import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const styles = readFileSync(new URL('../styles/live2d.css', import.meta.url), 'utf8');

describe('Live2D styles', () => {
  it('uses a white stage behind uploaded cover screenshots', () => {
    expect(styles).toMatch(/\.human-cover\s*{[\s\S]*background:\s*#ffffff;/);
    expect(styles).toMatch(/\.human-cover img\s*{[\s\S]*background:\s*#ffffff;/);
  });
});
