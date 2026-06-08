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

export function getAuditLogs(action = '', limit = 50) {
  return request.get('/api/audit-logs', { params: { action, limit } }) as Promise<{
    list: AuditLogRecord[];
    total: number;
  }>;
}
