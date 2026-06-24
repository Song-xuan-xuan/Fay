import { describe, expect, it } from 'vitest';
import { buildDigitalHumanRenderUrl } from './digitalHumanRenderUrl';
import type { DigitalHuman } from '../types';

const live2dHuman: DigitalHuman = {
  id: 'live2d_haru',
  name: 'Haru',
  type: 'live2d',
  cover_url: '',
  render_url: 'http://127.0.0.1:5174?model=Haru',
  voice: '',
  tags: [],
  persona: {},
  enabled: true,
};

describe('buildDigitalHumanRenderUrl', () => {
  it('adds Fay connection parameters for the message panel', () => {
    const url = buildDigitalHumanRenderUrl(live2dHuman, {
      token: 'jwt-token',
      username: 'alice',
      panel: 'message',
    });

    expect(url).toBe(
      'http://127.0.0.1:5174/?model=Haru&fay_token=jwt-token&fay_username=alice'
    );
  });

  it('keeps the same render profile for the dashboard/default panel', () => {
    const url = buildDigitalHumanRenderUrl(live2dHuman, {
      token: 'jwt-token',
      username: 'alice',
      panel: 'default',
    });

    expect(url).toBe(
      'http://127.0.0.1:5174/?model=Haru&fay_token=jwt-token&fay_username=alice'
    );
  });
});
