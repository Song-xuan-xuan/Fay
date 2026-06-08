import request, { postLegacyData } from './request';
import type { ExecutionStatus, MessageHistoryResponse, MessageRecord, SystemStatus, UserRecord } from '../types';

export interface ChatSession {
  id: number;
  user_id: number;
  username: string;
  title: string;
  started_at?: number;
  last_active_at?: number;
  message_count?: number;
  source?: string;
  deleted_at?: number | null;
}

interface RawMessageHistory {
  list?: MessageRecord[] | MessageRecord[][];
  total?: number;
  hasMore?: boolean;
}

export async function getMessageHistory(
  username: string,
  limit = 30,
  offset = 0,
  sessionId: number | null = null,
): Promise<MessageHistoryResponse> {
  const data = await postLegacyData<RawMessageHistory>('/api/get-msg', { username, limit, offset, session_id: sessionId });
  const rawList = Array.isArray(data.list) ? data.list : [];
  const list = rawList.flat() as MessageRecord[];
  return {
    list,
    total: Number(data.total || 0),
    hasMore: Boolean(data.hasMore),
  };
}

export function sendMessage(username: string, msg: string, sessionId: number | null = null) {
  return postLegacyData<{ result: string }>('/api/send', { username, msg, session_id: sessionId });
}

export async function getChatSessions(username?: string): Promise<ChatSession[]> {
  const params = username ? { username } : undefined;
  const data = await request.get('/api/chat-sessions', { params }) as { list?: ChatSession[] };
  return Array.isArray(data.list) ? data.list : [];
}

export function createChatSession(title: string, username?: string) {
  return request.post('/api/chat-sessions', { title, username }) as Promise<{ success: boolean; session: ChatSession }>;
}

export function renameChatSession(id: number, title: string) {
  return request.put(`/api/chat-sessions/${id}`, { title }) as Promise<{ success: boolean; session: ChatSession }>;
}

export function deleteChatSession(id: number, username?: string) {
  const params = username ? { username } : undefined;
  return request.delete(`/api/chat-sessions/${id}`, { params }) as Promise<{ success: boolean; deleted_messages: number }>;
}

export function getMessageById(id: number | string) {
  return request.post('/api/get-msg-by-id', { id }) as Promise<{ content: string }>;
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
