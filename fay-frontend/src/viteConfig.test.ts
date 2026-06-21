import { describe, expect, it } from 'vitest';
import viteConfigSource from '../vite.config.ts?raw';

describe('vite dev proxy', () => {
  it('does not proxy legacy Flask static assets into Vue', () => {
    expect(viteConfigSource).not.toContain("'/static'");
  });
});
