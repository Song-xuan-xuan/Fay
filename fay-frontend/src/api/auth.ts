import request from './request';
import type { AuthUser, ChangePasswordRequest, ChangePasswordResponse, LoginRequest, LoginResponse, RegisterRequest } from '../types/auth';

export function login(data: LoginRequest) {
  return request.post('/api/auth/login', data) as Promise<LoginResponse>;
}

export function register(data: RegisterRequest) {
  return request.post('/api/auth/register', data) as Promise<LoginResponse>;
}

export function logout() {
  return request.post('/api/auth/logout') as Promise<{ success: boolean }>;
}

export function getCurrentUser() {
  return request.get('/api/auth/me') as Promise<AuthUser>;
}

export function changePassword(data: ChangePasswordRequest) {
  return request.post('/api/auth/change-password', data) as Promise<ChangePasswordResponse>;
}

export function uploadAvatar(file: File) {
  const formData = new FormData();
  formData.append('avatar', file);
  return request.post('/api/auth/avatar', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }) as Promise<{ success: boolean; avatar_path: string }>;
}
