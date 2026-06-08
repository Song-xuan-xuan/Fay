export type AuthRole = 'admin' | 'user';

export interface AuthUser {
  uid: number;
  username: string;
  role: AuthRole;
  email?: string;
  avatar_path?: string;
  is_active?: number;
  must_change_password?: boolean;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest extends LoginRequest {
  email?: string;
}

export interface LoginResponse extends AuthUser {
  token: string;
  expires_in?: number;
  server_time?: number;
}

export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

export interface ChangePasswordResponse {
  success: boolean;
  token?: string;
}

export interface ManagedUser extends AuthUser {
  created_at?: number;
  last_login?: number | null;
  password_changed_at?: number | null;
}

export interface AuditLogRecord {
  id: number;
  user_id: number;
  username: string;
  action: string;
  resource?: string;
  details?: Record<string, unknown>;
  ip_address?: string;
  timestamp: number;
}
