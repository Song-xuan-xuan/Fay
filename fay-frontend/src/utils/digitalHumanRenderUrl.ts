import type { DigitalHuman } from '../types';
import { withFayConnectionParams } from './fayConnectionParams';

export type DigitalHumanPanelContext = 'default' | 'message';

interface BuildDigitalHumanRenderUrlOptions {
  token: string;
  username?: string;
  panel?: DigitalHumanPanelContext;
}

const CHAT_KEI_BASIC_VIEW_PARAMS = {
  view_scale: '0.38',
  view_x: '0.14',
  view_y: '0.26',
};

const RELATIVE_URL_BASE = 'http://fay.local';

function isRelativeUrl(url: string) {
  return url.startsWith('/') && !url.startsWith('//');
}

function isKeiBasicLive2d(human: DigitalHuman, url: URL) {
  return (
    human.type === 'live2d' &&
    (human.id === 'live2d_kei_basic_free' ||
      url.searchParams.get('model')?.toLowerCase() === 'kei_basic_free')
  );
}

function applyMessagePanelViewParams(human: DigitalHuman, renderUrl: string) {
  const trimmedUrl = renderUrl.trim();
  if (!trimmedUrl) {
    return renderUrl;
  }

  try {
    const relative = isRelativeUrl(trimmedUrl);
    const url = new URL(trimmedUrl, RELATIVE_URL_BASE);
    if (!isKeiBasicLive2d(human, url)) {
      return renderUrl;
    }

    Object.entries(CHAT_KEI_BASIC_VIEW_PARAMS).forEach(([key, value]) => {
      url.searchParams.set(key, value);
    });

    if (relative) {
      return `${url.pathname}${url.search}${url.hash}`;
    }
    return url.toString();
  } catch {
    return renderUrl;
  }
}

export function buildDigitalHumanRenderUrl(
  human: DigitalHuman,
  options: BuildDigitalHumanRenderUrlOptions
) {
  const panel = options.panel || 'default';
  const renderUrl =
    panel === 'message'
      ? applyMessagePanelViewParams(human, human.render_url)
      : human.render_url;

  return withFayConnectionParams(renderUrl, options.token, options.username || 'User');
}
