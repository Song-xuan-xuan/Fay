import { describe, expect, it } from 'vitest';
import viteConfigSource from '../vite.config.ts?raw';

describe('vite dev proxy', () => {
  it('does not proxy legacy Flask static assets into Vue', () => {
    expect(viteConfigSource).not.toContain("'/static'");
  });

  it('routes MCP and knowledge base APIs to the internal management service', () => {
    expect(viteConfigSource).toContain("const mcpTarget = env.VITE_MCP_PROXY_TARGET || 'http://127.0.0.1:5010';");

    const mcpRoute = viteConfigSource.indexOf("'/api/mcp'");
    const knowledgeRoute = viteConfigSource.indexOf("'/api/kb'");
    const flaskRoute = viteConfigSource.indexOf("'/api'");

    expect(mcpRoute).toBeGreaterThan(-1);
    expect(knowledgeRoute).toBeGreaterThan(-1);
    expect(flaskRoute).toBeGreaterThan(-1);
    expect(mcpRoute).toBeLessThan(flaskRoute);
    expect(knowledgeRoute).toBeLessThan(flaskRoute);
  });
});
