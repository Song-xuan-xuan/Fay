import axios from 'axios';
import { useAuthStore } from '../stores/auth';

function getMcpApiBaseUrl() {
  const configured = import.meta.env.VITE_MCP_API_BASE_URL;
  if (configured) return configured;
  return `http://${window.location.hostname}:5010`;
}

const mcpRequest = axios.create({
  baseURL: getMcpApiBaseUrl(),
  timeout: 20000,
  withCredentials: false,
});

mcpRequest.interceptors.request.use((config) => {
  const authStore = useAuthStore();
  if (authStore.token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${authStore.token}`;
  }
  return config;
});

mcpRequest.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const data = error.response?.data || {};
    const message = data.error || data.message || data.msg || error.message;
    return Promise.reject(new Error(message));
  },
);

export type McpTransport = 'sse' | 'stdio';

export interface McpServer {
  id: number;
  name: string;
  status: string;
  ip?: string;
  latency?: string;
  connection_time?: string;
  key?: string;
  transport?: McpTransport | string;
  command?: string;
  args?: string[];
  cwd?: string;
  env?: Record<string, string>;
  autostart?: boolean;
}

export interface McpTool {
  name: string;
  description?: string;
  inputSchema?: Record<string, unknown>;
  enabled?: boolean;
  available?: boolean;
  prestart?: boolean;
  prestart_params?: Record<string, unknown>;
  include_history?: boolean;
}

export interface McpResource {
  uri: string;
  name?: string;
  description?: string;
  text?: string;
  enabled?: boolean;
  server_id?: number;
  server_name?: string;
}

export interface McpServerPayload {
  name: string;
  transport: McpTransport;
  ip?: string;
  key?: string;
  command?: string;
  args?: string[];
  cwd?: string;
  env?: Record<string, string>;
  autostart?: boolean;
  auto_connect?: boolean;
  auto_reconnect?: boolean;
}

export interface McpServerActionResponse {
  success?: boolean;
  message?: string;
  server?: McpServer;
  tools?: McpTool[];
}

export function listMcpServers() {
  return mcpRequest.get('/api/mcp/servers') as Promise<McpServer[]>;
}

export function createMcpServer(payload: McpServerPayload) {
  return mcpRequest.post('/api/mcp/servers', payload, { timeout: 60000 }) as Promise<McpServerActionResponse>;
}

export function updateMcpServer(serverId: number, payload: McpServerPayload) {
  return mcpRequest.put(`/api/mcp/servers/${serverId}`, payload, { timeout: 60000 }) as Promise<McpServerActionResponse>;
}

export function deleteMcpServer(serverId: number) {
  return mcpRequest.delete(`/api/mcp/servers/${serverId}`) as Promise<McpServerActionResponse>;
}

export function connectMcpServer(serverId: number) {
  return mcpRequest.post(`/api/mcp/servers/${serverId}/connect`, {}, { timeout: 90000 }) as Promise<McpServerActionResponse>;
}

export function disconnectMcpServer(serverId: number) {
  return mcpRequest.post(`/api/mcp/servers/${serverId}/disconnect`) as Promise<McpServerActionResponse>;
}

export function getMcpServerTools(serverId: number) {
  return mcpRequest.get(`/api/mcp/servers/${serverId}/tools`) as Promise<{
    success: boolean;
    message?: string;
    tools: McpTool[];
  }>;
}

export function getMcpServerResources(serverId: number) {
  return mcpRequest.get(`/api/mcp/servers/${serverId}/resources`) as Promise<{
    success: boolean;
    message?: string;
    resources: McpResource[];
  }>;
}

export function toggleMcpTool(serverId: number, toolName: string, enabled: boolean) {
  return mcpRequest.post(`/api/mcp/servers/${serverId}/tools/${encodeURIComponent(toolName)}/toggle`, {
    enabled,
  }) as Promise<{ success: boolean; message?: string; tools?: McpTool[] }>;
}

export function toggleMcpResource(serverId: number, uri: string, enabled: boolean) {
  return mcpRequest.post(`/api/mcp/servers/${serverId}/resources/toggle`, {
    uri,
    enabled,
  }) as Promise<{ success: boolean; message?: string; uri?: string; enabled?: boolean }>;
}
