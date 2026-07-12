import { useState, useCallback, useEffect, useRef } from 'react';
import type { DashboardMetrics, SectorStatus } from '../types';
import { dashboardApi } from '../services/api/dashboard';

export function useDashboard(refreshInterval = 30000) {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [sectors, setSectors] = useState<SectorStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchMetrics = useCallback(async () => {
    try {
      setLoading(true);
      const [metricsData, sectorsData] = await Promise.all([
        dashboardApi.getOverview(),
        dashboardApi.getSectors(),
      ]);
      setMetrics(metricsData);
      setSectors(sectorsData);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch dashboard data');
    } finally {
      setLoading(false);
    }
  }, []);

  const refresh = useCallback(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  useEffect(() => {
    fetchMetrics();
    intervalRef.current = setInterval(fetchMetrics, refreshInterval);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [fetchMetrics, refreshInterval]);

  return { metrics, sectors, loading, error, refresh };
}
