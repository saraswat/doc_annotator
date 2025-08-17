import axios, { AxiosInstance } from 'axios';
import toast from 'react-hot-toast';

const API_URL = (process.env as any).REACT_APP_API_URL || 'http://localhost:8000/api';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.api.interceptors.request.use(
      (config: any) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error: any) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.api.interceptors.response.use(
      (response: any) => response,
      async (error: any) => {
        const originalRequest = error.config;
        
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          // Try to refresh token
          const refreshToken = localStorage.getItem('refresh_token');
          if (refreshToken) {
            try {
              const response = await this.api.post('/auth/refresh', { 
                refresh_token: refreshToken 
              });
              localStorage.setItem('access_token', response.data.access_token);
              
              // Retry original request
              originalRequest.headers.Authorization = `Bearer ${response.data.access_token}`;
              return this.api(originalRequest);
            } catch (refreshError) {
              // Refresh failed, redirect to login
              localStorage.removeItem('access_token');
              localStorage.removeItem('refresh_token');
              window.location.href = '/login';
              return Promise.reject(refreshError);
            }
          } else {
            // No refresh token, redirect to login
            window.location.href = '/login';
            return Promise.reject(error);
          }
        }

        // Show error toast for other errors
        if (error.response?.data?.detail) {
          toast.error(error.response.data.detail);
        } else if (error.message) {
          toast.error(error.message);
        }

        return Promise.reject(error);
      }
    );
  }

  get(url: string, params?: any, config?: any) {
    return this.api.get(url, { ...config, params });
  }

  post(url: string, data?: any, config?: any) {
    return this.api.post(url, data, config);
  }

  put(url: string, data?: any) {
    return this.api.put(url, data);
  }

  patch(url: string, data?: any) {
    return this.api.patch(url, data);
  }

  delete(url: string) {
    return this.api.delete(url);
  }

  postFormData(url: string, formData: FormData) {
    return this.api.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }
}

export default new ApiService();