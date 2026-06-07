import { describe, expect, it } from 'vitest';
import { detectWebglSupport } from './webgl';

describe('detectWebglSupport', () => {
  it('reports support when any WebGL context can be created', () => {
    const support = detectWebglSupport(() => ({
      getContext: (name: string) => (name === 'webgl' ? {} : null),
    }));

    expect(support.supported).toBe(true);
    expect(support.reason).toBe('available');
  });

  it('reports a clear failure when the browser returns no WebGL context', () => {
    const support = detectWebglSupport(() => ({
      getContext: () => null,
    }));

    expect(support.supported).toBe(false);
    expect(support.reason).toBe('context-unavailable');
    expect(support.message).toContain('WebGL');
  });

  it('keeps checking fallback contexts when one context creation fails', () => {
    const support = detectWebglSupport(() => ({
      getContext: (name: string) => {
        if (name === 'webgl2') throw new Error('webgl2 blocked');
        return name === 'webgl' ? {} : null;
      },
    }));

    expect(support.supported).toBe(true);
    expect(support.reason).toBe('available');
  });

  it('handles browser context creation errors without throwing', () => {
    const support = detectWebglSupport(() => ({
      getContext: () => {
        throw new Error('blocked');
      },
    }));

    expect(support.supported).toBe(false);
    expect(support.reason).toBe('context-error');
  });
});
