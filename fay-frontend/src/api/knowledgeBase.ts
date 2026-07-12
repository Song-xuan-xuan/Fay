import request from './request';

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
  return request.get('/api/kb/files') as Promise<KnowledgeBaseFileListResponse>;
}

export function uploadKnowledgeBaseFiles(files: File[]) {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));
  return request.post('/api/kb/files/upload', formData, {
    timeout: 120000,
  }) as Promise<KnowledgeBaseUploadResponse>;
}

export function deleteKnowledgeBaseFile(filename: string) {
  return request.delete(`/api/kb/files/${encodeURIComponent(filename)}`) as Promise<{
    success: boolean;
    deleted?: string;
  }>;
}

export function ingestKnowledgeBase(reset = false) {
  return request.post('/api/kb/ingest', { reset }, { timeout: 300000 }) as Promise<KnowledgeBaseActionResponse>;
}

export function queryKnowledgeBase(query: string, topK = 5) {
  return request.post('/api/kb/query', { query, top_k: topK }, { timeout: 120000 }) as Promise<KnowledgeBaseActionResponse>;
}

export function getKnowledgeBaseStats() {
  return request.get('/api/kb/stats') as Promise<KnowledgeBaseActionResponse>;
}
