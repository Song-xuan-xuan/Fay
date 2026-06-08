import { beforeEach, describe, expect, it, vi } from 'vitest';
import request from './request';
import {
  activateDigitalHuman,
  createDigitalHuman,
  deleteDigitalHuman,
  getActiveDigitalHuman,
  getDigitalHumans,
  importLive2dResourceHumans,
  updateDigitalHuman,
  uploadDigitalHumanCover,
} from './digitalHumans';

vi.mock('./request', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('digitalHumans API', () => {
  beforeEach(() => {
    vi.mocked(request.get).mockReset();
    vi.mocked(request.post).mockReset();
    vi.mocked(request.put).mockReset();
    vi.mocked(request.delete).mockReset();
  });

  it('uses the expected digital human endpoints', () => {
    getDigitalHumans({ keyword: '销售', type: 'iframe' });
    getActiveDigitalHuman();
    createDigitalHuman({ name: 'Fay', type: 'live2d' });
    updateDigitalHuman('dh_1', { name: 'Fay 2' });
    activateDigitalHuman('dh_1');
    importLive2dResourceHumans();
    deleteDigitalHuman('dh_1');

    expect(request.get).toHaveBeenNthCalledWith(1, '/api/digital-humans', { params: { keyword: '销售', type: 'iframe' } });
    expect(request.get).toHaveBeenNthCalledWith(2, '/api/digital-humans/active');
    expect(request.post).toHaveBeenNthCalledWith(1, '/api/digital-humans', { name: 'Fay', type: 'live2d' });
    expect(request.put).toHaveBeenCalledWith('/api/digital-humans/dh_1', { name: 'Fay 2' });
    expect(request.post).toHaveBeenNthCalledWith(2, '/api/digital-humans/dh_1/activate');
    expect(request.post).toHaveBeenNthCalledWith(3, '/api/digital-humans/import-live2d-resources', {});
    expect(request.delete).toHaveBeenCalledWith('/api/digital-humans/dh_1');
  });

  it('uploads covers using multipart form data', () => {
    const file = new File(['cover'], 'cover.png', { type: 'image/png' });

    uploadDigitalHumanCover('dh_1', file);

    expect(request.post).toHaveBeenCalledTimes(1);
    const [url, body, config] = vi.mocked(request.post).mock.calls[0];
    expect(url).toBe('/api/digital-humans/dh_1/cover');
    expect(body).toBeInstanceOf(FormData);
    expect(config).toEqual({ headers: { 'Content-Type': 'multipart/form-data' } });
  });
});
