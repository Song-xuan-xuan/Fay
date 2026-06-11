import request from './request';

export type DashboardRange = '7d' | '30d' | 'week' | 'month';
export type VisitorReportRange = DashboardRange | 'today';

export interface DashboardKpi {
  title: string;
  value: number | string;
  unit: string;
  source: string;
  is_demo?: boolean;
  change?: number;
}

export interface DashboardOverview {
  is_demo: boolean;
  data_source: string;
  kpis: DashboardKpi[];
  operations: Record<string, number>;
  users: DashboardUsers;
  tourism_source: DashboardTourismSource;
}

export interface DashboardTrendItem {
  date: string;
  services: number;
  questions: number;
  active_users: number;
}

export interface HotTopicItem {
  topic: string;
  count: number;
  ratio: number;
  representative_question: string;
  trend: number;
}

export interface DashboardTourismSource {
  row_count?: number;
  record_count?: number;
  imported_at?: number;
  import_status?: string;
  error?: string;
  file_path?: string;
  date_range?: { start: string; end: string };
}

export interface DashboardCountItem {
  date?: string;
  month?: string;
  name?: string;
  count: number;
}

export interface DashboardTourism {
  source: DashboardTourismSource;
  type_metrics: Array<{ name: string; visits: number; tourists: number; avg_satisfaction: number; avg_cost: number }>;
  attraction_ranking: Array<{ attraction_name: string; attraction_type: string; visits: number; avg_satisfaction: number; avg_cost: number }>;
  satisfaction_trend: Array<{ month: string; avg_satisfaction: number; low_ratio: number }>;
  visit_trend: Array<{ month: string; visits: number; tourists: number }>;
  satisfaction_distribution: Array<{ name: string; count: number }>;
  consumption_structure: { avg_total_cost: number; items: Array<{ name: string; value: number }> };
  tourist_profile: {
    age_groups: Array<{ name: string; count: number }>;
    gender_distribution: Array<{ name: string; count: number }>;
  };
  details: Array<{ visit_date: string; tourist_id: string; attraction_name: string; attraction_type: string; tourist_segment?: string; total_cost: number; satisfaction: number }>;
  average_satisfaction: number;
  low_satisfaction_count: number;
}

export interface DashboardUsers {
  total_users: number;
  today_new_users: number;
  week_new_users: number;
  week_active_users: number;
  active_users: number;
  role_distribution: Array<{ role: string; count: number }>;
  registration_trend: Array<{ date: string; count: number }>;
  active_trend: Array<{ date: string; count: number }>;
  recent_users: Array<{ uid: number; username: string; role: string; email: string; created_at?: number; last_login?: number; is_active?: number }>;
}

export interface TourismFilters {
  start_date?: string;
  end_date?: string;
  attraction_type?: string;
  attraction_name?: string;
  satisfaction_min?: number | string;
  satisfaction_max?: number | string;
  tourist_segment?: string;
}

export interface VisitorReportAction {
  id: number;
  report_id: number;
  action_type: string;
  title: string;
  description: string;
  status: 'pending' | 'processing' | 'done' | 'ignored';
  created_at: number;
}

export interface VisitorReportEvidence {
  id: number;
  report_id: number;
  msg_id: number;
  session_id: number;
  uid: number;
  username: string;
  topic: string;
  sentiment_label: string;
  sentiment_score: number;
  risk_level: string;
  resolved_status: string;
  is_complaint: number;
  evidence_text: string;
  reply_text: string;
  created_at: number;
}

export interface VisitorReport {
  id: number;
  title: string;
  report_type: string;
  range_key: string;
  range_start: number;
  range_end: number;
  status: string;
  metrics: {
    message_count: number;
    complaint_count: number;
    unresolved_count: number;
    escalated_count: number;
    negative_ratio: number;
    sentiments: Record<string, number>;
    topics: Record<string, number>;
    risks: Record<string, number>;
    top_topics: Array<{ topic: string; count: number }>;
    tourism?: Record<string, unknown>;
  };
  report_text: string;
  suggestions: VisitorReportAction[];
  actions?: VisitorReportAction[];
  created_by: string;
  created_at: number;
}

export interface VisitorReportGeneratePayload {
  range?: VisitorReportRange;
  range_key?: VisitorReportRange;
  start_ms?: number;
  end_ms?: number;
}

export function getDashboardOverview(range: DashboardRange) {
  return request.get('/api/dashboard/overview', { params: { range } }) as Promise<DashboardOverview>;
}

export function getDashboardServiceTrends(range: DashboardRange) {
  return request.get('/api/dashboard/service-trends', { params: { range } }) as Promise<{ range: DashboardRange; items: DashboardTrendItem[] }>;
}

export function getDashboardHotTopics(range: DashboardRange) {
  return request.get('/api/dashboard/hot-topics', { params: { range } }) as Promise<{ range: DashboardRange; items: HotTopicItem[] }>;
}

export function getDashboardTourism(filters: TourismFilters) {
  return request.get('/api/dashboard/tourism', { params: filters }) as Promise<DashboardTourism>;
}

export function getDashboardUsers() {
  return request.get('/api/dashboard/users') as Promise<DashboardUsers>;
}

export function reimportDashboardTourism() {
  return request.post('/api/dashboard/tourism/reimport', {}, { timeout: 300000 }) as Promise<Record<string, unknown>>;
}

export function explainDashboard(payload: Record<string, unknown>) {
  return request.post('/api/dashboard/explain', payload, { timeout: 60000 }) as Promise<{ text: string }>;
}

export function generateVisitorReport(payload: VisitorReportGeneratePayload) {
  return request.post('/api/dashboard/visitor-report/generate', payload, { timeout: 120000 }) as Promise<VisitorReport>;
}

export function getLatestVisitorReport() {
  return request.get('/api/dashboard/visitor-report/latest') as Promise<VisitorReport | Record<string, never>>;
}

export function listVisitorReports(limit = 20) {
  return request.get('/api/dashboard/visitor-report/list', { params: { limit } }) as Promise<{ items: VisitorReport[] }>;
}

export function getVisitorReport(id: number) {
  return request.get(`/api/dashboard/visitor-report/${id}`) as Promise<VisitorReport>;
}

export function getVisitorReportEvidence(id: number) {
  return request.get(`/api/dashboard/visitor-report/${id}/evidence`) as Promise<{ items: VisitorReportEvidence[] }>;
}

export function exportVisitorReport(id: number, format: 'md' | 'html') {
  return request.get(`/api/dashboard/visitor-report/${id}/export`, {
    params: { format },
    responseType: 'text',
  }) as Promise<string>;
}

export function updateVisitorReportActionStatus(id: number, status: VisitorReportAction['status']) {
  return request.post(`/api/dashboard/visitor-report/action/${id}/status`, { status }) as Promise<VisitorReportAction>;
}
