import { beforeEach, describe, expect, it, vi } from 'vitest';
import request from './request';
import { cleanupAuditLogs, getAuditLogs } from './users';

vi.mock('./request', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('users API', () => {
  beforeEach(() => {
    vi.mocked(request.get).mockReset();
    vi.mocked(request.post).mockReset();
  });

  it('converts audit log page options to limit and offset params', () => {
    getAuditLogs({ action: 'password_reset', username: 'alice', page: 3, pageSize: 20 });

    expect(request.get).toHaveBeenCalledWith('/api/audit-logs', {
      params: {
        action: 'password_reset',
        username: 'alice',
        limit: 20,
        offset: 40,
      },
    });
  });

  it('posts audit cleanup requests with the retention days', () => {
    cleanupAuditLogs(90);

    expect(request.post).toHaveBeenCalledWith('/api/audit-logs/cleanup', { days: 90 });
  });
});
