import { describe, expect, it } from 'vitest';
import { buildDigitalHumanRenderUrl } from './digitalHumanRenderUrl';
import type { DigitalHuman } from '../types';

const keiBasic: DigitalHuman = {
  id: 'live2d_kei_basic_free',
  name: 'Kei Basic',
  type: 'live2d',
  cover_url: '',
  render_url: 'http://127.0.0.1:5174?model=kei_basic_free',
  voice: '',
  tags: [],
  persona: {},
  enabled: true,
};

describe('buildDigitalHumanRenderUrl', () => {
  it('adds a smaller Kei Basic view profile for the message panel only', () => {
    const url = buildDigitalHumanRenderUrl(keiBasic, {
      token: 'jwt-token',
      username: 'alice',
      panel: 'message',
    });

    expect(url).toBe(
      'http://127.0.0.1:5174/?model=kei_basic_free&view_scale=0.38&view_x=0.14&view_y=0.26&fay_token=jwt-token&fay_username=alice'
    );
  });

  it('keeps the dashboard/default panel profile unchanged', () => {
    const url = buildDigitalHumanRenderUrl(keiBasic, {
      token: 'jwt-token',
      username: 'alice',
      panel: 'default',
    });

    expect(url).toBe(
      'http://127.0.0.1:5174/?model=kei_basic_free&fay_token=jwt-token&fay_username=alice'
    );
  });
});
