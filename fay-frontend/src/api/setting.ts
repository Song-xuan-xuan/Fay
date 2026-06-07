import request, { postLegacyData } from './request';
import type { ConfigDataResponse, FayConfig } from '../types';

export function getData() {
  return request.post('/api/get-data') as Promise<ConfigDataResponse>;
}

export function submitConfig(config: FayConfig) {
  return postLegacyData<{ result: string; message?: string }>('/api/submit', { config });
}

export function startLive() {
  return request.post('/api/start-live') as Promise<{ result: string }>;
}

export function stopLive() {
  return request.post('/api/stop-live') as Promise<{ result: string }>;
}

export function getRunStatus() {
  return request.post('/api/get-run-status') as Promise<{ status: boolean }>;
}

export function clearMemory() {
  return request.post('/api/clear-memory') as Promise<{ success: boolean; message: string }>;
}

export function startGenagents(instruction: string) {
  return request.post('/api/start-genagents', { instruction }) as Promise<{
    success: boolean;
    message: string;
    url?: string;
  }>;
}
