import axios from 'axios';
import { useAuthStore } from '../stores/auth';

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_PATH || '',
  timeout: 15000,
  withCredentials: true,
});

request.interceptors.request.use((config) => {
  const authStore = useAuthStore();
  if (authStore.token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${authStore.token}`;
  }
  return config;
});

request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      const authStore = useAuthStore();
      authStore.clearSession();
      const current = `${window.location.pathname}${window.location.search}`;
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = `/login?redirect=${encodeURIComponent(current)}`;
      }
    }
    const message = error.response?.data?.message || error.response?.data?.msg || error.response?.data?.error || error.message;
    return Promise.reject(new Error(message));
  },
);

export function postLegacyData<T>(url: string, payload: unknown): Promise<T> {
  const body = new URLSearchParams();
  body.set('data', JSON.stringify(payload));
  return request.post(url, body, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  }) as Promise<T>;
}

export default request;
