import { Card, CardContent, Box, Typography, SvgIcon } from '@mui/material';
import { TrendingUp, TrendingDown } from '@mui/icons-material';
import { AreaChart, Area, ResponsiveContainer } from 'recharts';

interface MetricsCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend?: { value: number; isPositive: boolean };
  sparklineData?: { value: number }[];
  color?: string;
}

export default function MetricsCard({ title, value, icon, trend, sparklineData, color = '#1a237e' }: MetricsCardProps) {
  return (
    <Card sx={{ height: '100%', position: 'relative', overflow: 'hidden' }}>
      <CardContent sx={{ p: 2.5 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box>
            <Typography variant="body2" color="text.secondary" fontWeight={500} gutterBottom>{title}</Typography>
            <Typography variant="h4" fontWeight={700}>{value}</Typography>
            {trend && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mt: 0.5 }}>
                {trend.isPositive ? (
                  <TrendingUp sx={{ fontSize: 16, color: 'success.main' }} />
                ) : (
                  <TrendingDown sx={{ fontSize: 16, color: 'error.main' }} />
                )}
                <Typography variant="caption" color={trend.isPositive ? 'success.main' : 'error.main'} fontWeight={600}>
                  {trend.value}%
                </Typography>
              </Box>
            )}
          </Box>
          <Box sx={{
            width: 48, height: 48, borderRadius: 2, display: 'flex', alignItems: 'center', justifyContent: 'center',
            backgroundColor: `${color}20`, color: color,
          }}>
            {icon}
          </Box>
        </Box>
        {sparklineData && sparklineData.length > 0 && (
          <Box sx={{ height: 40, mt: 1 }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={sparklineData}>
                <defs>
                  <linearGradient id={`gradient-${title}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={color} stopOpacity={0.3} />
                    <stop offset="100%" stopColor={color} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <Area type="monotone" dataKey="value" stroke={color} fill={`url(#gradient-${title})`} strokeWidth={2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
