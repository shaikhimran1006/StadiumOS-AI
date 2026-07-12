import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react';
import type { Stadium, Sector, DashboardMetrics } from '../types';
import { dashboardApi } from '../services/api/dashboard';

interface StadiumContextType {
  currentStadium: Stadium | null;
  sectors: Sector[];
  metrics: DashboardMetrics | null;
  loading: boolean;
  setCurrentStadium: (stadium: Stadium) => void;
  refreshMetrics: () => Promise<void>;
}

const StadiumContext = createContext<StadiumContextType | undefined>(undefined);

export function StadiumProvider({ children }: { children: ReactNode }) {
  const [currentStadium, setCurrentStadium] = useState<Stadium | null>(() => {
    const saved = localStorage.getItem('stadiumos_stadium');
    return saved ? JSON.parse(saved) : null;
  });
  const [sectors, setSectors] = useState<Sector[]>([]);
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(false);

  const refreshMetrics = useCallback(async () => {
    try {
      setLoading(true);
      const data = await dashboardApi.getOverview();
      setMetrics(data);
      const sectorsData = await dashboardApi.getSectors();
      setSectors(sectorsData);
    } catch (error) {
      console.error('Failed to refresh metrics:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleSetStadium = useCallback((stadium: Stadium) => {
    setCurrentStadium(stadium);
    localStorage.setItem('stadiumos_stadium', JSON.stringify(stadium));
  }, []);

  useEffect(() => {
    refreshMetrics();
    const interval = setInterval(refreshMetrics, 60000);
    return () => clearInterval(interval);
  }, [refreshMetrics]);

  return (
    <StadiumContext.Provider
      value={{ currentStadium, sectors, metrics, loading, setCurrentStadium: handleSetStadium, refreshMetrics }}
    >
      {children}
    </StadiumContext.Provider>
  );
}

export function useStadiumContext(): StadiumContextType {
  const context = useContext(StadiumContext);
  if (!context) throw new Error('useStadiumContext must be used within StadiumProvider');
  return context;
}
