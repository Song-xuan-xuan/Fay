import { describe, expect, it } from 'vitest';
import source from './request.ts?raw';

describe('request authentication redirect', () => {
  it('does not redirect the public homepage when an optional request returns 401', () => {
    expect(source).toContain("const isPublicPage = window.location.pathname === '/'");
    expect(source).toContain('if (!isPublicPage && !window.location.pathname.startsWith');
  });
});
