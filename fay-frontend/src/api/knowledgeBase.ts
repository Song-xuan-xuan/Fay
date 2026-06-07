import axios from 'axios';

function getMcpApiBaseUrl() {
  const configured = import.meta.env.VITE_MCP_API_BASE_URL;
  if (configured) {
    return configured;
  }
  return `http://${window.location.hostname}:5010`;
}

const mcpRequest = axios.create({
  baseURL: getMcpApiBaseUrl(),
  timeout: 15000,
  withCredentials: false,
});

mcpRequest.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const data = error.response?.data || {};
    const message = data.error || data.message || data.msg || error.message;
    return Promise.reject(new Error(message));
  },
);

export interface KnowledgeBaseFile {
  name: string;
  size: number;
  mtime?: string;
}

export interface KnowledgeBaseFileListResponse {
  success: boolean;
  library_dir: string;
  files: KnowledgeBaseFile[];
}

export interface KnowledgeBaseUploadResponse {
  success: boolean;
  library_dir: string;
  files: Array<Pick<KnowledgeBaseFile, 'name' | 'size'>>;
  errors?: Array<{ name: string; error: string }>;
}

export interface KnowledgeBaseActionResponse {
  success: boolean;
  result?: unknown;
  error?: string;
  library_dir?: string;
}

export function listKnowledgeBaseFiles() {
  return mcpRequest.get('/api/kb/files') as Promise<KnowledgeBaseFileListResponse>;
}

export function uploadKnowledgeBaseFiles(files: File[]) {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
  return mcpRequest.post('/api/kb/files/upload', formData, {
    timeout: 120000,
  }) as Promise<KnowledgeBaseUploadResponse>;
}

export function deleteKnowledgeBaseFile(filename: string) {
  return mcpRequest.delete(`/api/kb/files/${encodeURIComponent(filename)}`) as Promise<{
    success: boolean;
    deleted?: string;
  }>;
}

export function ingestKnowledgeBase(reset = false) {
  return mcpRequest.post('/api/kb/ingest', { reset }, { timeout: 300000 }) as Promise<KnowledgeBaseActionResponse>;
}

export function queryKnowledgeBase(query: string, topK = 5) {
  return mcpRequest.post('/api/kb/query', { query, top_k: topK }, { timeout: 120000 }) as Promise<KnowledgeBaseActionResponse>;
}

export function getKnowledgeBaseStats() {
  return mcpRequest.get('/api/kb/stats') as Promise<KnowledgeBaseActionResponse>;
}
