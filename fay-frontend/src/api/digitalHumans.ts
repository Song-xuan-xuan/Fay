import request from './request';
import type { DigitalHuman, DigitalHumanPayload, DigitalHumanType } from '../types';

export interface DigitalHumanListParams {
  keyword?: string;
  type?: DigitalHumanType | '';
}

export interface DigitalHumanListResponse {
  success: boolean;
  items: DigitalHuman[];
  active: DigitalHuman | null;
  active_id: string;
}

export function getDigitalHumans(params: DigitalHumanListParams = {}) {
  return request.get('/api/digital-humans', { params }) as Promise<DigitalHumanListResponse>;
}

export function getActiveDigitalHuman() {
  return request.get('/api/digital-humans/active') as Promise<{ success: boolean; digital_human: DigitalHuman }>;
}

export function createDigitalHuman(payload: DigitalHumanPayload) {
  return request.post('/api/digital-humans', payload) as Promise<{ success: boolean; digital_human: DigitalHuman }>;
}

export function updateDigitalHuman(id: string, payload: DigitalHumanPayload) {
  return request.put(`/api/digital-humans/${id}`, payload) as Promise<{ success: boolean; digital_human: DigitalHuman }>;
}

export function deleteDigitalHuman(id: string) {
  return request.delete(`/api/digital-humans/${id}`) as Promise<{ success: boolean; digital_human: DigitalHuman }>;
}

export function activateDigitalHuman(id: string) {
  return request.post(`/api/digital-humans/${id}/activate`) as Promise<{ success: boolean; digital_human: DigitalHuman }>;
}

export function importLive2dResourceHumans() {
  return request.post('/api/digital-humans/import-live2d-resources', {}) as Promise<{
    success: boolean;
    imported: DigitalHuman[];
    skipped: DigitalHuman[];
    items: DigitalHuman[];
  }>;
}

export function uploadDigitalHumanCover(id: string, file: File) {
  const body = new FormData();
  body.set('cover', file);
  return request.post(`/api/digital-humans/${id}/cover`, body, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }) as Promise<{ success: boolean; cover_url: string; digital_human: DigitalHuman }>;
}
