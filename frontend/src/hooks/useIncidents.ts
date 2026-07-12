import { useState, useCallback, useEffect } from 'react';
import type { Incident } from '../types';
import { incidentsApi } from '../services/api/incidents';

export function useIncidents() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchIncidents = useCallback(async (params?: { status?: string; category?: string; priority?: string }) => {
    try {
      setLoading(true);
      const response = await incidentsApi.list({ page, pageSize: 20, ...params });
      setIncidents(response.data);
      setTotal(response.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch incidents');
    } finally {
      setLoading(false);
    }
  }, [page]);

  const createIncident = useCallback(async (incident: Partial<Incident>) => {
    const newIncident = await incidentsApi.create(incident);
    setIncidents((prev) => [newIncident, ...prev]);
    return newIncident;
  }, []);

  const assignIncident = useCallback(async (id: string, assigneeId: string) => {
    const updated = await incidentsApi.assign(id, assigneeId);
    setIncidents((prev) => prev.map((i) => (i.id === id ? updated : i)));
    return updated;
  }, []);

  const resolveIncident = useCallback(async (id: string, resolution: string) => {
    const updated = await incidentsApi.resolve(id, resolution);
    setIncidents((prev) => prev.map((i) => (i.id === id ? updated : i)));
    return updated;
  }, []);

  const addIncidentUpdate = useCallback(async (id: string, message: string) => {
    const updated = await incidentsApi.addUpdate(id, message);
    setIncidents((prev) => prev.map((i) => (i.id === id ? updated : i)));
    return updated;
  }, []);

  const deleteIncident = useCallback(async (id: string) => {
    await incidentsApi.delete(id);
    setIncidents((prev) => prev.filter((i) => i.id !== id));
  }, []);

  useEffect(() => {
    fetchIncidents();
  }, [fetchIncidents]);

  return {
    incidents, total, page, setPage, loading, error,
    fetchIncidents, createIncident, assignIncident, resolveIncident, addIncidentUpdate, deleteIncident,
  };
}
