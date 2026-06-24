import request from './request';

export interface BackgroundItem {
  id: string;
  name: string;
  url: string;
  builtin?: boolean;
  filename?: string;
  created_at?: number;
}

export interface BackgroundListResponse {
  success: boolean;
  items: BackgroundItem[];
  active: BackgroundItem;
  active_id: string;
}

export function getBackgrounds() {
  return request.get('/api/backgrounds') as Promise<BackgroundListResponse>;
}

export function activateBackground(id: string) {
  return request.post(`/api/backgrounds/${id}/activate`) as Promise<BackgroundListResponse>;
}

export function deleteBackground(id: string) {
  return request.delete(`/api/backgrounds/${id}`) as Promise<{
    success: boolean;
    background: BackgroundItem;
    active: BackgroundItem;
    active_id: string;
  }>;
}

export function uploadBackground(file: File, name = '') {
  const body = new FormData();
  body.set('background', file);
  if (name.trim()) {
    body.set('name', name.trim());
  }
  return request.post('/api/backgrounds', body, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }) as Promise<BackgroundListResponse & { background: BackgroundItem }>;
}
