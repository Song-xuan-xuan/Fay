import { describe, expect, it } from 'vitest';
import source from './Login.vue?raw';

describe('Login authentication feedback', () => {
  it('shows the backend error when login or registration fails', () => {
    expect(source).toContain('catch (error)');
    expect(source).toContain('ElMessage.error');
    expect(source).toContain("error instanceof Error && error.message");
  });
});
