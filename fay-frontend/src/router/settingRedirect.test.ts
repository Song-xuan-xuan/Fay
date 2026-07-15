import { describe, expect, it } from 'vitest';
import routerSource from './index.ts?raw';

describe('legacy setting route', () => {
  it('redirects the old persona page to the digital human library', () => {
    expect(routerSource).toContain("path: '/setting'");
    expect(routerSource).toContain("redirect: '/app/live2d'");
    expect(routerSource).not.toContain("name: 'setting', component: Setting");
  });
});
