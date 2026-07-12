import apiClient from './client';
import type { Event, PaginatedResponse } from '../../types';

export const eventsApi = {
  async list(params?: { page?: number; pageSize?: number; status?: string; type?: string }): Promise<PaginatedResponse<Event>> {
    const { data } = await apiClient.get('/events', { params });
    return data;
  },

  async getById(id: string): Promise<Event> {
    const { data } = await apiClient.get(`/events/${id}`);
    return data;
  },

  async create(event: Partial<Event>): Promise<Event> {
    const { data } = await apiClient.post('/events', event);
    return data;
  },

  async update(id: string, event: Partial<Event>): Promise<Event> {
    const { data } = await apiClient.put(`/events/${id}`, event);
    return data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/events/${id}`);
  },

  async getLiveEvents(): Promise<Event[]> {
    const { data } = await apiClient.get('/events/live');
    return data;
  },

  async getUpcomingEvents(): Promise<Event[]> {
    const { data } = await apiClient.get('/events/upcoming');
    return data;
  },
};
