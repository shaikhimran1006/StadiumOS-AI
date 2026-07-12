import apiClient from './client';
import type { DashboardMetrics, SectorStatus } from '../../types';

export const dashboardApi = {
  async getOverview(): Promise<DashboardMetrics> {
    const { data } = await apiClient.get('/dashboard/overview');
    return data;
  },

  async getSectors(): Promise<SectorStatus[]> {
    const { data } = await apiClient.get('/dashboard/sectors');
    return data;
  },

  async getStadiumInfo(): Promise<{ name: string; capacity: number; occupancy: number }> {
    const { data } = await apiClient.get('/dashboard/stadium');
    return data;
  },

  async getAnalytics(params?: { startDate?: string; endDate?: string; metric?: string }): Promise<Record<string, unknown>> {
    const { data } = await apiClient.get('/dashboard/analytics', { params });
    return data;
  },

  async getOccupancyTrend(hours = 24): Promise<{ time: string; value: number }[]> {
    const { data } = await apiClient.get('/dashboard/occupancy-trend', { params: { hours } });
    return data;
  },
};
