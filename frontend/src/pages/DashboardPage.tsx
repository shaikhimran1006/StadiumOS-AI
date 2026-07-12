import { Box, Grid, Typography, Button } from '@mui/material';
import { Warning, ReportProblem, Event, People, SmartToy, Speed, TrendingUp, Timer } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import MetricsCard from '../components/dashboard/MetricsCard';
import AlertsPanel from '../components/dashboard/AlertsPanel';
import IncidentsPanel from '../components/dashboard/IncidentsPanel';
import OccupancyChart from '../components/dashboard/OccupancyChart';
import SectorGrid from '../components/dashboard/SectorGrid';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { useDashboard } from '../hooks/useDashboard';
import { useAlerts } from '../hooks/useAlerts';
import { useIncidents } from '../hooks/useIncidents';

export default function DashboardPage() {
  const navigate = useNavigate();
  const { metrics, sectors, loading: dashboardLoading } = useDashboard();
  const { alerts } = useAlerts();
  const { incidents } = useIncidents();

  if (dashboardLoading && !metrics) return <LoadingSpinner fullScreen message="Loading dashboard..." />;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" fontWeight={700}>Dashboard</Typography>
          <Typography variant="body2" color="text.secondary">Real-time stadium operations overview</Typography>
        </Box>
        <Button variant="contained" color="secondary" onClick={() => navigate('/chat')}>
          <SmartToy sx={{ mr: 1 }} /> AI Assistant
        </Button>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} lg={3}>
          <MetricsCard
            title="Active Alerts"
            value={metrics?.activeAlerts || alerts.length}
            icon={<Warning />}
            trend={{ value: 12, isPositive: false }}
            color="#d32f2f"
            sparklineData={[{ value: 5 }, { value: 8 }, { value: 6 }, { value: 10 }, { value: 7 }, { value: metrics?.activeAlerts || 4 }]}
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <MetricsCard
            title="Active Incidents"
            value={metrics?.activeIncidents || incidents.length}
            icon={<ReportProblem />}
            trend={{ value: 5, isPositive: false }}
            color="#ed6c02"
            sparklineData={[{ value: 3 }, { value: 5 }, { value: 4 }, { value: 6 }, { value: 3 }, { value: metrics?.activeIncidents || 2 }]}
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <MetricsCard
            title="Occupancy Rate"
            value={`${metrics?.occupancyRate || 72}%`}
            icon={<People />}
            trend={{ value: 8, isPositive: true }}
            color="#2e7d32"
            sparklineData={[{ value: 45000 }, { value: 52000 }, { value: 58000 }, { value: 61000 }, { value: 57000 }, { value: 57600 }]}
          />
        </Grid>
        <Grid item xs={12} sm={6} lg={3}>
          <MetricsCard
            title="AI Interactions"
            value={metrics?.aiInteractions || 1284}
            icon={<SmartToy />}
            trend={{ value: 23, isPositive: true }}
            color="#1a237e"
            sparklineData={[{ value: 800 }, { value: 950 }, { value: 1100 }, { value: 1050 }, { value: 1200 }, { value: 1284 }]}
          />
        </Grid>
      </Grid>

      <Grid container spacing={3} sx={{ mt: 1 }}>
        <Grid item xs={12} lg={8}>
          <OccupancyChart
            data={metrics?.occupancyTrend || [
              { time: '00:00', value: 0 }, { time: '04:00', value: 2000 },
              { time: '08:00', value: 15000 }, { time: '12:00', value: 45000 },
              { time: '16:00', value: 62000 }, { time: '20:00', value: 75000 },
              { time: '23:59', value: 50000 },
            ]}
          />
        </Grid>
        <Grid item xs={12} lg={4}>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <MetricsCard
              title="Avg Response Time"
              value={`${metrics?.avgResponseTime || 2.3}s`}
              icon={<Timer />}
              trend={{ value: 15, isPositive: true }}
              color="#0288d1"
            />
            <MetricsCard
              title="Live Events"
              value={metrics?.liveEvents || 1}
              icon={<Event />}
              color="#9c27b0"
            />
          </Box>
        </Grid>
      </Grid>

      <Grid container spacing={3} sx={{ mt: 1 }}>
        <Grid item xs={12} lg={6}>
          <AlertsPanel alerts={alerts} maxItems={5} />
        </Grid>
        <Grid item xs={12} lg={6}>
          <IncidentsPanel incidents={incidents} maxItems={5} />
        </Grid>
      </Grid>

      <Box sx={{ mt: 3 }}>
        <SectorGrid sectors={sectors as never[]} />
      </Box>
    </Box>
  );
}
