import apiClient from './client';
import type { Alert, PaginatedResponse } from '../../types';

export const alertsApi = {
  async list(params?: { page?: number; pageSize?: number; severity?: string; status?: string; type?: string }): Promise<PaginatedResponse<Alert>> {
    const { data } = await apiClient.get('/alerts', { params });
    return data;
  },

  async getById(id: string): Promise<Alert> {
    const { data } = await apiClient.get(`/alerts/${id}`);
    return data;
  },

  async create(alert: Partial<Alert>): Promise<Alert> {
    const { data } = await apiClient.post('/alerts', alert);
    return data;
  },

  async update(id: string, alert: Partial<Alert>): Promise<Alert> {
    const { data } = await apiClient.put(`/alerts/${id}`, alert);
    return data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/alerts/${id}`);
  },

  async escalate(id: string, reason: string): Promise<Alert> {
    const { data } = await apiClient.post(`/alerts/${id}/escalate`, { reason });
    return data;
  },

  async resolve(id: string, resolution: string): Promise<Alert> {
    const { data } = await apiClient.post(`/alerts/${id}/resolve`, { resolution });
    return data;
  },

  async acknowledge(id: string): Promise<Alert> {
    const { data } = await apiClient.post(`/alerts/${id}/acknowledge`);
    return data;
  },
};
