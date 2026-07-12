import { describe, expect, it } from 'vitest';
import knowledgeBaseSource from './knowledgeBase.ts?raw';
import mcpSource from './mcp.ts?raw';

describe('management API routing', () => {
  it.each([
    ['knowledge base', knowledgeBaseSource],
    ['MCP', mcpSource],
  ])('uses the shared authenticated request client for %s APIs', (_name, source) => {
    expect(source).toContain("import request from './request';");
    expect(source).not.toContain("from 'axios'");
    expect(source).not.toContain('axios.create');
    expect(source).not.toContain('VITE_MCP_API_BASE_URL');
    expect(source).not.toContain(':5010');
  });
});
