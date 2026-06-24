import type { DigitalHuman } from '../types';
import { withFayConnectionParams } from './fayConnectionParams';

export type DigitalHumanPanelContext = 'default' | 'message';

interface BuildDigitalHumanRenderUrlOptions {
  token: string;
  username?: string;
  panel?: DigitalHumanPanelContext;
}

export function buildDigitalHumanRenderUrl(
  human: DigitalHuman,
  options: BuildDigitalHumanRenderUrlOptions
) {
  return withFayConnectionParams(human.render_url, options.token, options.username || 'User');
}
