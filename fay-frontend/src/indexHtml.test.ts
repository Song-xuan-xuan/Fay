import { describe, expect, it } from 'vitest';
import indexHtml from '../index.html?raw';

describe('frontend index.html assets', () => {
  it('loads the favicon from Vue public assets', () => {
    expect(indexHtml).toContain('href="/frontend-static/brand/favicon.ico"');
    expect(indexHtml).not.toContain('/static/');
  });

  it('uses a Vite brand placeholder for the document title', () => {
    expect(indexHtml).toContain('<title>%BRAND_CONSOLE_NAME%</title>');
    expect(indexHtml).not.toContain('Fay 管理台');
  });
});
