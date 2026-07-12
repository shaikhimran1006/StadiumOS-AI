import apiClient from './client';
import type { Feedback, PaginatedResponse } from '../../types';

export const feedbackApi = {
  async submit(feedback: { rating: number; category: string; message: string }): Promise<Feedback> {
    const { data } = await apiClient.post('/feedback', feedback);
    return data;
  },

  async list(params?: { page?: number; pageSize?: number; category?: string; sentiment?: string }): Promise<PaginatedResponse<Feedback>> {
    const { data } = await apiClient.get('/feedback', { params });
    return data;
  },

  async getAnalytics(): Promise<{ averageRating: number; total: number; byCategory: Record<string, number>; sentiment: Record<string, number> }> {
    const { data } = await apiClient.get('/feedback/analytics');
    return data;
  },

  async delete(id: string): Promise<void> {
    await apiClient.delete(`/feedback/${id}`);
  },
};
