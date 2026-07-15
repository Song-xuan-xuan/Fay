import request from './request';
import type { DigitalHumanType } from '../types';

export interface PublicDigitalHuman {
  name: string;
  type: DigitalHumanType;
  render_url: string;
  cover_url: string;
}

export function getPublicDigitalHuman() {
  return request.get('/api/public/digital-human') as Promise<{
    success: boolean;
    digital_human: PublicDigitalHuman;
  }>;
}
