import apiClient from '../api/client';
import type { User } from '../../types';

export const authService = {
  async loginWithGoogle(): Promise<User> {
    return new Promise((resolve) => {
      const width = 500;
      const height = 600;
      const left = window.screenX + (window.outerWidth - width) / 2;
      const top = window.screenY + (window.outerHeight - height) / 2;

      const popup = window.open(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/auth/google`,
        'google-oauth',
        `width=${width},height=${height},left=${left},top=${top}`
      );

      const handler = (event: MessageEvent) => {
        if (event.data?.type === 'google-auth-success') {
          const { token, user } = event.data;
          localStorage.setItem('stadiumos_token', token);
          window.removeEventListener('message', handler);
          popup?.close();
          resolve(user);
        }
        if (event.data?.type === 'google-auth-error') {
          window.removeEventListener('message', handler);
          popup?.close();
          throw new Error('Google authentication failed');
        }
      };

      window.addEventListener('message', handler);
    });
  },

  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout');
    } finally {
      localStorage.removeItem('stadiumos_token');
    }
  },

  async refreshToken(): Promise<string> {
    const { data } = await apiClient.post('/auth/refresh');
    localStorage.setItem('stadiumos_token', data.token);
    return data.token;
  },

  async getCurrentUser(): Promise<User> {
    const { data } = await apiClient.get('/auth/me');
    return data;
  },
};
