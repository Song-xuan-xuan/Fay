import { describe, expect, it } from 'vitest';
import { isNavItemActive } from './navigation';

describe('isNavItemActive', () => {
  it('activates the message item only on the root path', () => {
    expect(isNavItemActive('/', { to: '/', exact: true })).toBe(true);
    expect(isNavItemActive('/setting', { to: '/', exact: true })).toBe(false);
    expect(isNavItemActive('/mcp', { to: '/', exact: true })).toBe(false);
  });

  it('activates non-root items on their route and nested routes', () => {
    expect(isNavItemActive('/setting', { to: '/setting' })).toBe(true);
    expect(isNavItemActive('/setting/profile', { to: '/setting' })).toBe(true);
    expect(isNavItemActive('/knowledge', { to: '/setting' })).toBe(false);
  });
});
