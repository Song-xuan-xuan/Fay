import request from './request';

export interface RecommendationAttraction {
  id?: number;
  name: string;
  category?: string;
  summary?: string;
  tags?: string[];
  visit_minutes?: number;
  difficulty?: number;
  indoor?: boolean;
  accessibility?: string;
  budget_level?: string;
  popularity?: number;
  satisfaction?: number;
  enabled?: boolean;
}

export interface RecommendationTemplate {
  id?: number;
  name: string;
  summary?: string;
  interest_tags?: string[];
  duration_minutes?: number;
  intensity?: string;
  budget_level?: string;
  enabled?: boolean;
}

export interface RecommendationStop {
  id?: number;
  template_id?: number;
  attraction_id: number;
  order_index: number;
  stay_minutes: number;
  note?: string;
}

export interface RecommendationEdge {
  id?: number;
  from_attraction_id: number;
  to_attraction_id: number;
  walk_minutes?: number;
  distance_meters?: number;
  difficulty?: number;
  accessibility?: string;
  bidirectional?: boolean;
  notes?: string;
  enabled?: boolean;
}

export interface RecommendationMaterial {
  id?: number;
  attraction_id: number;
  interest_tag?: string;
  title?: string;
  focus?: string;
  script?: string;
}

export interface RecommendationRequest {
  interests: string[];
  free_text?: string;
  arrival_time?: string;
  departure_time?: string;
  time_budget_minutes?: number;
  intensity?: string;
  companions?: string;
  budget_level?: string;
  start_attraction?: string;
  end_attraction?: string;
  avoid_items?: string[];
  indoor_preference?: string;
}

export interface RecommendationResult {
  recommendation_id?: number;
  main_route: RecommendationRoute | null;
  alternatives: RecommendationRoute[];
  adjustment_actions?: string[];
}

export interface RecommendationRoute {
  id: number;
  name: string;
  summary: string;
  score: number;
  score_breakdown: Record<string, number>;
  duration_minutes: number;
  walk_minutes: number;
  intensity: string;
  budget_level?: string;
  risks: string[];
  stops: RecommendationRouteStop[];
}

export interface RecommendationRouteStop {
  id: number;
  name: string;
  category: string;
  tags: string[];
  walk_minutes: number;
  stay_minutes: number;
  start_time: string;
  end_time: string;
  difficulty: number;
  indoor: boolean;
  explanation_focus: string;
  script: string;
}

export function createRecommendation(payload: RecommendationRequest) {
  return request.post('/api/recommendation/recommend', payload, { timeout: 120000 }) as Promise<RecommendationResult>;
}

export function getRecommendationPreferences() {
  return request.get('/api/recommendation/preferences') as Promise<{ success: boolean; preferences: Record<string, unknown> | null }>;
}

export function saveRecommendationPreferences(payload: Partial<RecommendationRequest>) {
  return request.put('/api/recommendation/preferences', payload) as Promise<{ success: boolean; preferences: Record<string, unknown> }>;
}

export function deleteRecommendationPreferences() {
  return request.delete('/api/recommendation/preferences') as Promise<{ success: boolean }>;
}

export function listRecommendationHistory(limit = 20) {
  return request.get('/api/recommendation/history', { params: { limit } }) as Promise<{ success: boolean; items: Array<Record<string, unknown>> }>;
}

export function getRecommendationHistoryDetail(id: number) {
  return request.get(`/api/recommendation/history/${id}`) as Promise<{ success: boolean; item: Record<string, unknown> }>;
}

export function submitRecommendationFeedback(payload: Record<string, unknown>) {
  return request.post('/api/recommendation/feedback', payload) as Promise<{ success: boolean; feedback: Record<string, unknown> }>;
}

export function listRecommendationAttractions() {
  return request.get('/api/recommendation/admin/attractions') as Promise<{ success: boolean; items: RecommendationAttraction[] }>;
}

export function createRecommendationAttraction(payload: RecommendationAttraction) {
  return request.post('/api/recommendation/admin/attractions', payload) as Promise<{ success: boolean; id: number }>;
}

export function updateRecommendationAttraction(id: number, payload: RecommendationAttraction) {
  return request.put(`/api/recommendation/admin/attractions/${id}`, payload) as Promise<{ success: boolean; id: number }>;
}

export function deleteRecommendationAttraction(id: number) {
  return request.delete(`/api/recommendation/admin/attractions/${id}`) as Promise<{ success: boolean }>;
}

export function listRecommendationTemplates() {
  return request.get('/api/recommendation/admin/templates') as Promise<{ success: boolean; items: RecommendationTemplate[] }>;
}

export function createRecommendationTemplate(payload: RecommendationTemplate) {
  return request.post('/api/recommendation/admin/templates', payload) as Promise<{ success: boolean; id: number }>;
}

export function updateRecommendationTemplate(id: number, payload: RecommendationTemplate) {
  return request.put(`/api/recommendation/admin/templates/${id}`, payload) as Promise<{ success: boolean; id: number }>;
}

export function deleteRecommendationTemplate(id: number) {
  return request.delete(`/api/recommendation/admin/templates/${id}`) as Promise<{ success: boolean }>;
}

export function listRecommendationStops(templateId: number) {
  return request.get(`/api/recommendation/admin/templates/${templateId}/stops`) as Promise<{ success: boolean; items: RecommendationStop[] }>;
}

export function createRecommendationStop(templateId: number, payload: RecommendationStop) {
  return request.post(`/api/recommendation/admin/templates/${templateId}/stops`, payload) as Promise<{ success: boolean; id: number }>;
}

export function deleteRecommendationStop(id: number) {
  return request.delete(`/api/recommendation/admin/stops/${id}`) as Promise<{ success: boolean }>;
}

export function listRecommendationEdges() {
  return request.get('/api/recommendation/admin/edges') as Promise<{ success: boolean; items: RecommendationEdge[] }>;
}

export function createRecommendationEdge(payload: RecommendationEdge) {
  return request.post('/api/recommendation/admin/edges', payload) as Promise<{ success: boolean; id: number }>;
}

export function deleteRecommendationEdge(id: number) {
  return request.delete(`/api/recommendation/admin/edges/${id}`) as Promise<{ success: boolean }>;
}

export function listRecommendationMaterials() {
  return request.get('/api/recommendation/admin/materials') as Promise<{ success: boolean; items: RecommendationMaterial[] }>;
}

export function createRecommendationMaterial(payload: RecommendationMaterial) {
  return request.post('/api/recommendation/admin/materials', payload) as Promise<{ success: boolean; id: number }>;
}

export function deleteRecommendationMaterial(id: number) {
  return request.delete(`/api/recommendation/admin/materials/${id}`) as Promise<{ success: boolean }>;
}

export function getRecommendationConfig() {
  return request.get('/api/recommendation/admin/config') as Promise<{ success: boolean; config: Record<string, unknown> }>;
}

export function updateRecommendationConfig(payload: Record<string, unknown>) {
  return request.put('/api/recommendation/admin/config', payload) as Promise<{ success: boolean; config: Record<string, unknown> }>;
}

export function exportRecommendationData() {
  return request.get('/api/recommendation/admin/export') as Promise<Record<string, unknown>>;
}

export function importRecommendationData(payload: Record<string, unknown>) {
  return request.post('/api/recommendation/admin/import', payload, { timeout: 120000 }) as Promise<Record<string, unknown>>;
}

export function initializeRecommendationAttractions(limit = 100) {
  return request.post('/api/recommendation/admin/initialize-attractions', { limit }) as Promise<Record<string, unknown>>;
}

export function listRecommendationLogs(limit = 50) {
  return request.get('/api/recommendation/admin/logs', { params: { limit } }) as Promise<{ success: boolean; items: Array<Record<string, unknown>> }>;
}

export function importRecommendationAttractionFile(file: File, dryRun = false) {
  const form = new FormData();
  form.append('file', file);
  return request.post('/api/recommendation/admin/attractions/import', form, {
    params: { dry_run: dryRun ? 1 : 0 },
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  }) as Promise<Record<string, unknown>>;
}

export function exportRecommendationAttractions(format: 'csv' | 'xlsx' = 'csv') {
  return request.get('/api/recommendation/admin/attractions/export', {
    params: { format },
    responseType: 'blob',
  }) as Promise<Blob>;
}
