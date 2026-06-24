import { beforeEach, describe, expect, it, vi } from 'vitest';
import request from './request';
import {
  activateBackground,
  deleteBackground,
  getBackgrounds,
  uploadBackground,
} from './backgrounds';

vi.mock('./request', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('backgrounds API', () => {
  beforeEach(() => {
    vi.mocked(request.get).mockReset();
    vi.mocked(request.post).mockReset();
    vi.mocked(request.delete).mockReset();
  });

  it('uses the expected background management endpoints', () => {
    getBackgrounds();
    activateBackground('bg_1');
    deleteBackground('bg_1');

    expect(request.get).toHaveBeenCalledWith('/api/backgrounds');
    expect(request.post).toHaveBeenCalledWith('/api/backgrounds/bg_1/activate');
    expect(request.delete).toHaveBeenCalledWith('/api/backgrounds/bg_1');
  });

  it('uploads backgrounds using multipart form data', () => {
    const file = new File(['image'], 'lobby.png', { type: 'image/png' });

    uploadBackground(file, '大厅背景');

    expect(request.post).toHaveBeenCalledTimes(1);
    const [url, body, config] = vi.mocked(request.post).mock.calls[0];
    expect(url).toBe('/api/backgrounds');
    expect(body).toBeInstanceOf(FormData);
    expect((body as FormData).get('name')).toBe('大厅背景');
    expect(config).toEqual({ headers: { 'Content-Type': 'multipart/form-data' } });
  });
});
