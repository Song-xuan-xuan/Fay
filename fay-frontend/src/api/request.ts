import axios from 'axios';

const request = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_PATH || '',
  timeout: 15000,
  withCredentials: true,
});

request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.message || error.response?.data?.msg || error.message;
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
