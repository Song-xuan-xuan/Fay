import request from './request';
import type { AuditLogRecord, AuthRole, ManagedUser } from '../types/auth';

export interface CreateUserPayload {
  username: string;
  password: string;
  role: AuthRole;
  email?: string;
}

export interface UpdateUserPayload {
  role?: AuthRole;
  email?: string;
  is_active?: boolean;
}

export interface AuditLogQuery {
  action?: string;
  username?: string;
  page?: number;
  pageSize?: number;
}

export function getUsers() {
  return request.get('/api/users') as Promise<{ list: ManagedUser[] }>;
}

export function createUser(data: CreateUserPayload) {
  return request.post('/api/users', data) as Promise<{ success: boolean; uid: number; user: ManagedUser }>;
}

export function updateUser(uid: number, data: UpdateUserPayload) {
  return request.put(`/api/users/${uid}`, data) as Promise<{ success: boolean; user: ManagedUser }>;
}

export function deleteUserById(uid: number) {
  return request.delete(`/api/users/${uid}`) as Promise<{ success: boolean }>;
}

export function resetUserPassword(uid: number, new_password: string) {
  return request.post(`/api/users/${uid}/reset-password`, { new_password }) as Promise<{ success: boolean }>;
}

export function getAuditLogs(query?: AuditLogQuery): Promise<{ list: AuditLogRecord[]; total: number }>;
export function getAuditLogs(action?: string, limit?: number): Promise<{ list: AuditLogRecord[]; total: number }>;
export function getAuditLogs(queryOrAction: AuditLogQuery | string = {}, limit = 50) {
  const query = typeof queryOrAction === 'string' ? { action: queryOrAction, pageSize: limit } : queryOrAction;
  const page = Math.max(1, Number(query.page || 1));
  const pageSize = Math.max(1, Number(query.pageSize || limit));
  const params: Record<string, string | number> = {
    limit: pageSize,
    offset: (page - 1) * pageSize,
  };
  if (query.action) params.action = query.action;
  if (query.username) params.username = query.username;
  return request.get('/api/audit-logs', { params }) as Promise<{
    list: AuditLogRecord[];
    total: number;
  }>;
}

export function cleanupAuditLogs(days = 90) {
  return request.post('/api/audit-logs/cleanup', { days }) as Promise<{
    success: boolean;
    deleted: number;
    days: number;
  }>;
}
