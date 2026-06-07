import { startLive, stopLive, getRunStatus } from './setting';

export function getDefaultLive2dUrl(_currentPort = window.location.port): string {
  return 'http://127.0.0.1:5174';
}

export function getLive2dUrl(): string {
  const configured = import.meta.env.VITE_LIVE2D_URL;
  if (configured) {
    return configured;
  }
  return getDefaultLive2dUrl();
}

export const liveApi = {
  getRunStatus,
  startLive,
  stopLive,
};
