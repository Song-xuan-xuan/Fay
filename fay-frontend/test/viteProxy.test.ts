import { describe, expect, it } from 'vitest';
import viteConfig from '../vite.config';

async function resolveViteConfig() {
  if (typeof viteConfig === 'function') {
    return viteConfig({ command: 'serve', mode: 'development' } as never);
  }
  return viteConfig;
}

describe('vite dev proxy', () => {
  it('proxies digital human resource files to Flask', async () => {
    const config = await resolveViteConfig();
    const proxy = config.server?.proxy as Record<string, unknown>;

    expect(proxy['/digital-humans']).toMatchObject({
      target: 'http://127.0.0.1:5000',
      changeOrigin: true,
    });
  });

  it('proxies uploaded background images to Flask', async () => {
    const config = await resolveViteConfig();
    const proxy = config.server?.proxy as Record<string, unknown>;

    expect(proxy['/backgrounds']).toMatchObject({
      target: 'http://127.0.0.1:5000',
      changeOrigin: true,
    });
  });
});
