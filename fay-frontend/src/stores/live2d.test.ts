import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createPinia, setActivePinia } from 'pinia';
import { useLive2dStore } from './live2d';
import { activateDigitalHuman, getDigitalHumans } from '../api/digitalHumans';

vi.mock('../api/digitalHumans', () => ({
  activateDigitalHuman: vi.fn(),
  getDigitalHumans: vi.fn(),
}));

describe('useLive2dStore digital human state', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.mocked(getDigitalHumans).mockReset();
    vi.mocked(activateDigitalHuman).mockReset();
  });

  it('loads items and computes the active digital human', async () => {
    vi.mocked(getDigitalHumans).mockResolvedValue({
      success: true,
      active_id: 'teacher',
      active: {
        id: 'teacher',
        name: '讲师',
        type: 'image',
        cover_url: '/cover/teacher.png',
        render_url: '',
        voice: 'zh-CN-XiaoyiNeural',
        tags: ['教培'],
        persona: { goal: '提供知识' },
        enabled: true,
      },
      items: [
        {
          id: 'teacher',
          name: '讲师',
          type: 'image',
          cover_url: '/cover/teacher.png',
          render_url: '',
          voice: 'zh-CN-XiaoyiNeural',
          tags: ['教培'],
          persona: { goal: '提供知识' },
          enabled: true,
        },
      ],
    });
    const store = useLive2dStore();

    await store.loadDigitalHumans();

    expect(store.activeId).toBe('teacher');
    expect(store.activeHuman?.name).toBe('讲师');
    expect(store.activeRenderUrl).toBe('');
    expect(store.items).toHaveLength(1);
  });

  it('updates the active human after activation', async () => {
    vi.mocked(activateDigitalHuman).mockResolvedValue({
      success: true,
      digital_human: {
        id: 'sales',
        name: '销售顾问',
        type: 'iframe',
        cover_url: '/cover/sales.png',
        render_url: 'http://127.0.0.1:7001',
        voice: '温柔女声',
        tags: ['销售'],
        persona: { goal: '促成交易' },
        enabled: true,
      },
    });
    const store = useLive2dStore();

    await store.activateDigitalHuman('sales');

    expect(store.activeId).toBe('sales');
    expect(store.activeHuman?.render_url).toBe('http://127.0.0.1:7001');
    expect(store.items[0].id).toBe('sales');
  });

  it('does not change the active id when receiving a non-active human update', () => {
    const store = useLive2dStore();
    store.activeId = 'teacher';
    store.items = [
      {
        id: 'teacher',
        name: '讲师',
        type: 'image',
        cover_url: '/cover/teacher.png',
        render_url: '',
        voice: 'zh-CN-XiaoyiNeural',
        tags: ['教培'],
        persona: { goal: '提供知识' },
        enabled: true,
      },
    ];

    store.receiveDigitalHuman({
      id: 'sales',
      name: '销售顾问',
      type: 'iframe',
      cover_url: '/cover/sales.png',
      render_url: 'http://127.0.0.1:7001',
      voice: '温柔女声',
      tags: ['销售'],
      persona: { goal: '促成交易' },
      enabled: true,
    });

    expect(store.activeId).toBe('teacher');
    expect(store.activeHuman?.name).toBe('讲师');
    expect(store.items.some((item) => item.id === 'sales')).toBe(true);
  });
});
