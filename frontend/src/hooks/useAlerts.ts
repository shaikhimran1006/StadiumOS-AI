import { useState, useCallback, useEffect } from 'react';
import type { Alert } from '../types';
import { alertsApi } from '../services/api/alerts';

export function useAlerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAlerts = useCallback(async (params?: { severity?: string; status?: string; type?: string }) => {
    try {
      setLoading(true);
      const response = await alertsApi.list({ page, pageSize: 20, ...params });
      setAlerts(response.data);
      setTotal(response.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch alerts');
    } finally {
      setLoading(false);
    }
  }, [page]);

  const createAlert = useCallback(async (alert: Partial<Alert>) => {
    const newAlert = await alertsApi.create(alert);
    setAlerts((prev) => [newAlert, ...prev]);
    return newAlert;
  }, []);

  const acknowledgeAlert = useCallback(async (id: string) => {
    const updated = await alertsApi.acknowledge(id);
    setAlerts((prev) => prev.map((a) => (a.id === id ? updated : a)));
    return updated;
  }, []);

  const resolveAlert = useCallback(async (id: string, resolution: string) => {
    const updated = await alertsApi.resolve(id, resolution);
    setAlerts((prev) => prev.map((a) => (a.id === id ? updated : a)));
    return updated;
  }, []);

  const escalateAlert = useCallback(async (id: string, reason: string) => {
    const updated = await alertsApi.escalate(id, reason);
    setAlerts((prev) => prev.map((a) => (a.id === id ? updated : a)));
    return updated;
  }, []);

  const deleteAlert = useCallback(async (id: string) => {
    await alertsApi.delete(id);
    setAlerts((prev) => prev.filter((a) => a.id !== id));
  }, []);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  return {
    alerts, total, page, setPage, loading, error,
    fetchAlerts, createAlert, acknowledgeAlert, resolveAlert, escalateAlert, deleteAlert,
  };
}
