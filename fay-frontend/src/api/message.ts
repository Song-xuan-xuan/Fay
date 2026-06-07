import request, { postLegacyData } from './request';
import type { ExecutionStatus, MessageHistoryResponse, MessageRecord, SystemStatus, UserRecord } from '../types';

interface RawMessageHistory {
  list?: MessageRecord[] | MessageRecord[][];
  total?: number;
  hasMore?: boolean;
}

export async function getMessageHistory(
  username: string,
  limit = 30,
  offset = 0,
): Promise<MessageHistoryResponse> {
  const data = await postLegacyData<RawMessageHistory>('/api/get-msg', { username, limit, offset });
  const rawList = Array.isArray(data.list) ? data.list : [];
  const list = rawList.flat() as MessageRecord[];
  return {
    list,
    total: Number(data.total || 0),
    hasMore: Boolean(data.hasMore),
  };
}

export function sendMessage(username: string, msg: string) {
  return postLegacyData<{ result: string }>('/api/send', { username, msg });
}

export function getMessageById(id: number | string) {
  return request.post('/api/get-msg-by-id', { id }) as Promise<{ content: string }>;
}

export function adoptMessage(id: number | string) {
  return request.post('/api/adopt-msg', { id }) as Promise<{ status: string; msg: string }>;
}

export function unadoptMessage(id: number | string) {
  return request.post('/api/unadopt-msg', { id }) as Promise<{
    status: string;
    msg: string;
    unadopted_ids?: Array<number | string>;
  }>;
}

export async function getMemberList(): Promise<UserRecord[]> {
  const data = await request.post('/api/get-member-list') as { list?: UserRecord[] };
  return Array.isArray(data.list) ? data.list : [];
}

export function addUser(username: string) {
  return request.post('/api/add-user', { username }) as Promise<{ success: boolean; message: string; uid?: number }>;
}

export function deleteUser(username: string) {
  return request.post('/api/delete-user', { username }) as Promise<{ success: boolean; message: string }>;
}

export function getUserExtraInfo(username: string) {
  return request.post('/api/get-user-extra-info', { username }) as Promise<{ success: boolean; extra_info?: string }>;
}

export function updateUserExtraInfo(username: string, extra_info: string) {
  return request.post('/api/update-user-extra-info', { username, extra_info }) as Promise<{
    success: boolean;
    message?: string;
  }>;
}

export function getUserPortrait(username: string) {
  return request.post('/api/get-user-portrait', { username }) as Promise<{ success: boolean; user_portrait?: string }>;
}

export function updateUserPortrait(username: string, user_portrait: string) {
  return request.post('/api/update-user-portrait', { username, user_portrait }) as Promise<{
    success: boolean;
    message?: string;
  }>;
}

export function openImage(path: string) {
  return request.post('/api/open-image', { path }) as Promise<{ success: boolean; message?: string }>;
}

export function getSystemStatus(username: string) {
  return request.get('/api/get-system-status', { params: { username } }) as Promise<SystemStatus>;
}

export function getAudioConfig() {
  return request.get('/api/get-audio-config') as Promise<{ mic: boolean; speaker: boolean }>;
}

export function getExecutionStatus(username: string) {
  return request.get('/api/execution-status', { params: { username } }) as Promise<ExecutionStatus>;
}

export function cancelExecution(username: string) {
  return request.post('/api/execution-cancel', { username }) as Promise<{ success: boolean }>;
}
