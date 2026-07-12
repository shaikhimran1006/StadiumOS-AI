import { useState, useEffect } from 'react';
import { Box, Typography, Grid, Card, CardContent, Select, MenuItem, FormControl, InputLabel } from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, Legend } from 'recharts';
import { dashboardApi } from '../services/api/dashboard';
import LoadingSpinner from '../components/common/LoadingSpinner';

const COLORS = ['#1a237e', '#283593', '#f9a825', '#2e7d32', '#d32f2f', '#9c27b0', '#0288d1', '#ed6c02'];

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState('7d');
  const [analytics, setAnalytics] = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, [timeRange]);

  const loadAnalytics = async () => {
    try {
      setLoading(true);
      const data = await dashboardApi.getAnalytics({ metric: timeRange });
      setAnalytics(data);
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  }

  const alertsByType = (analytics?.alertsByType as { type: string; count: number }[]) || [
    { type: 'Security', count: 12 }, { type: 'Medical', count: 8 }, { type: 'Fire', count: 3 },
    { type: 'Crowd', count: 15 }, { type: 'Technical', count: 6 }, { type: 'Weather', count: 2 },
  ];

  const incidentsByCategory = (analytics?.incidentsByCategory as { category: string; count: number }[]) || [
    { category: 'Security', count: 8 }, { category: 'Medical', count: 5 }, { category: 'Fire', count: 2 },
    { category: 'Structural', count: 1 }, { category: 'Crowd', count: 10 }, { category: 'Equipment', count: 4 },
  ];

  const hourlyTraffic = [
    { hour: '6AM', visitors: 5000, alerts: 2 }, { hour: '8AM', visitors: 15000, alerts: 5 },
    { hour: '10AM', visitors: 35000, alerts: 8 }, { hour: '12PM', visitors: 52000, alerts: 12 },
    { hour: '2PM', visitors: 65000, alerts: 15 }, { hour: '4PM', visitors: 72000, alerts: 10 },
    { hour: '6PM', visitors: 78000, alerts: 7 }, { hour: '8PM', visitors: 60000, alerts: 4 },
    { hour: '10PM', visitors: 30000, alerts: 2 }, { hour: '12AM', visitors: 5000, alerts: 1 },
  ];

  const responseTimeData = [
    { day: 'Mon', time: 2.1 }, { day: 'Tue', time: 1.8 }, { day: 'Wed', time: 2.5 },
    { day: 'Thu', time: 1.5 }, { day: 'Fri', time: 2.8 }, { day: 'Sat', time: 3.2 },
    { day: 'Sun', time: 2.0 },
  ];

  if (loading) return <LoadingSpinner message="Loading analytics..." />;

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" fontWeight={700}>Analytics</Typography>
          <Typography variant="body2" color="text.secondary">Performance insights and trends</Typography>
        </Box>
        <FormControl size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Time Range</InputLabel>
          <Select value={timeRange} label="Time Range" onChange={(e) => setTimeRange(e.target.value)}>
            <MenuItem value="24h">Last 24 Hours</MenuItem>
            <MenuItem value="7d">Last 7 Days</MenuItem>
            <MenuItem value="30d">Last 30 Days</MenuItem>
            <MenuItem value="90d">Last 90 Days</MenuItem>
          </Select>
        </FormControl>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>Visitor Traffic & Alerts</Typography>
              <Box sx={{ height: 350 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={hourlyTraffic}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis dataKey="hour" tick={{ fontSize: 12, fill: '#9e9e9e' }} />
                    <YAxis yAxisId="left" tick={{ fontSize: 12, fill: '#9e9e9e' }} />
                    <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 12, fill: '#9e9e9e' }} />
                    <Tooltip contentStyle={{ backgroundColor: '#1a1f4a', border: '1px solid #2a2f5a', borderRadius: 8 }} />
                    <Legend />
                    <Bar yAxisId="left" dataKey="visitors" fill="#1a237e" radius={[4, 4, 0, 0]} name="Visitors" />
                    <Bar yAxisId="right" dataKey="alerts" fill="#d32f2f" radius={[4, 4, 0, 0]} name="Alerts" />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>Alerts by Type</Typography>
              <Box sx={{ height: 350, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={alertsByType} dataKey="count" nameKey="type" cx="50%" cy="50%" outerRadius={100} label={({ type, count }) => `${type}: ${count}`}>
                      {alertsByType.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={{ backgroundColor: '#1a1f4a', border: '1px solid #2a2f5a', borderRadius: 8 }} />
                  </PieChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>Incidents by Category</Typography>
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={incidentsByCategory} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis type="number" tick={{ fontSize: 12, fill: '#9e9e9e' }} />
                    <YAxis type="category" dataKey="category" tick={{ fontSize: 12, fill: '#9e9e9e' }} width={100} />
                    <Tooltip contentStyle={{ backgroundColor: '#1a1f4a', border: '1px solid #2a2f5a', borderRadius: 8 }} />
                    <Bar dataKey="count" fill="#f9a825" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Typography variant="subtitle1" fontWeight={600} gutterBottom>AI Response Time (sec)</Typography>
              <Box sx={{ height: 300 }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={responseTimeData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                    <XAxis dataKey="day" tick={{ fontSize: 12, fill: '#9e9e9e' }} />
                    <YAxis tick={{ fontSize: 12, fill: '#9e9e9e' }} />
                    <Tooltip contentStyle={{ backgroundColor: '#1a1f4a', border: '1px solid #2a2f5a', borderRadius: 8 }} />
                    <Line type="monotone" dataKey="time" stroke="#2e7d32" strokeWidth={2} dot={{ fill: '#2e7d32' }} />
                  </LineChart>
                </ResponsiveContainer>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
