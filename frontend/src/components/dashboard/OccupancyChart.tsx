import { Card, CardContent, CardHeader, Typography, Box } from '@mui/material';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface OccupancyChartProps {
  data: { time: string; value: number }[];
  capacity?: number;
}

export default function OccupancyChart({ data, capacity = 80000 }: OccupancyChartProps) {
  const formattedData = data.map((d) => ({
    ...d,
    occupancy: d.value,
    capacity,
  }));

  return (
    <Card sx={{ height: '100%' }}>
      <CardHeader
        title={<Typography variant="subtitle1" fontWeight={600}>Stadium Occupancy</Typography>}
        subheader={<Typography variant="caption" color="text.secondary">Real-time occupancy trend</Typography>}
      />
      <CardContent>
        <Box sx={{ height: 300 }}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={formattedData}>
              <defs>
                <linearGradient id="occupancyGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#1a237e" stopOpacity={0.4} />
                  <stop offset="100%" stopColor="#1a237e" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="time" tick={{ fontSize: 12, fill: '#9e9e9e' }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fontSize: 12, fill: '#9e9e9e' }} tickLine={false} axisLine={false} tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
              <Tooltip
                contentStyle={{ backgroundColor: '#1a1f4a', border: '1px solid #2a2f5a', borderRadius: 8 }}
                labelStyle={{ color: '#9e9e9e' }}
                formatter={(value: number) => [`${value.toLocaleString()} visitors`, 'Occupancy']}
              />
              <Area type="monotone" dataKey="occupancy" stroke="#1a237e" fill="url(#occupancyGradient)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </Box>
      </CardContent>
    </Card>
  );
}
