import apiClient from './client';
import type { Incident, PaginatedResponse } from '../../types';

export const incidentsApi = {
  async list(params?: { page?: number; pageSize?: number; status?: string; category?: string; priority?: string }): Promise<PaginatedResponse<Incident>> {
    const { data } = await apiClient.get('/incidents', { params });
    return data;
  },

  async getById(id: string): Promise<Incident> {
    const { data } = await apiClient.get(`/incidents/${id}`);
    return data;
  },

  async create(incident: Partial<Incident>): Promise<Incident> {
    const { data } = await apiClient.post('/incidents', incident);
    return data;
  },

  async update(id: string, incident: Partial<Incident>): Promise<Incident> {
    const { data } = await apiClient.put(`/incidents/${id}`, incident);
    return data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/incidents/${id}`);
  },

  async assign(id: string, assigneeId: string): Promise<Incident> {
    const { data } = await apiClient.post(`/incidents/${id}/assign`, { assigneeId });
    return data;
  },

  async resolve(id: string, resolution: string): Promise<Incident> {
    const { data } = await apiClient.post(`/incidents/${id}/resolve`, { resolution });
    return data;
  },

  async addUpdate(id: string, message: string): Promise<Incident> {
    const { data } = await apiClient.post(`/incidents/${id}/updates`, { message });
    return data;
  },
};
