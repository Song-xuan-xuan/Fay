import { describe, expect, it } from 'vitest';
import source from './Mcp.vue?raw';

describe('Mcp settings view', () => {
  it('mounts the background manager inside the settings group page', () => {
    expect(source).toContain('BackgroundManager');
    expect(source).toContain('mcp-background-manager');
  });
});
