import { describe, expect, it } from 'vitest';
import { getDefaultLive2dUrl } from './live';

describe('getDefaultLive2dUrl', () => {
  it('uses the independent Live2D service in dev instead of nesting the console', () => {
    expect(getDefaultLive2dUrl('5173')).toBe('http://127.0.0.1:5174');
  });

  it('does not fall back to the Fay console port in production serving', () => {
    expect(getDefaultLive2dUrl('5000')).toBe('http://127.0.0.1:5174');
  });
});
