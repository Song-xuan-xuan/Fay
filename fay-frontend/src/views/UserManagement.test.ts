import { describe, expect, it } from 'vitest';
import source from './UserManagement.vue?raw';

describe('UserManagement view', () => {
  it('renders the create-user dialog outside the clipped users panel', () => {
    expect(source).toMatch(/<el-dialog[^>]*title="新建用户"[^>]*append-to-body/s);
  });
});
