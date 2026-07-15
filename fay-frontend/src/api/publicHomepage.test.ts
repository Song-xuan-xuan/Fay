import { beforeEach, describe, expect, it, vi } from 'vitest';
import request from './request';
import { getPublicDigitalHuman } from './publicHomepage';

vi.mock('./request', () => ({ default: { get: vi.fn() } }));

describe('public homepage API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads the sanitized public digital human endpoint', () => {
    getPublicDigitalHuman();
    expect(request.get).toHaveBeenCalledWith('/api/public/digital-human');
  });
});
