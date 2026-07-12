import { Card, CardContent, CardHeader, Typography, Box, Grid } from '@mui/material';
import type { SectorStatus } from '../../types';

interface SectorGridProps {
  sectors: SectorStatus[];
  onSectorClick?: (sector: SectorStatus) => void;
}

const statusColors: Record<string, string> = {
  normal: '#2e7d32',
  warning: '#f9a825',
  critical: '#d32f2f',
  closed: '#616161',
};

export default function SectorGrid({ sectors, onSectorClick }: SectorGridProps) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardHeader
        title={<Typography variant="subtitle1" fontWeight={600}>Sector Overview</Typography>}
        subheader="Occupancy heatmap by sector"
      />
      <CardContent>
        <Grid container spacing={1.5}>
          {sectors.map((sector) => {
            const occupancyPercent = sector.occupancyPercent || Math.round((sector.occupancy / sector.capacity) * 100);
            const color = statusColors[sector.status] || '#2e7d32';

            return (
              <Grid item xs={6} sm={4} md={3} key={sector.id}>
                <Box
                  onClick={() => onSectorClick?.(sector)}
                  sx={{
                    p: 2, borderRadius: 2, cursor: 'pointer', textAlign: 'center',
                    border: `1px solid ${color}40`,
                    backgroundColor: `${color}15`,
                    transition: 'all 0.2s',
                    '&:hover': { transform: 'translateY(-2px)', boxShadow: `0 4px 12px ${color}30` },
                  }}
                >
                  <Typography variant="caption" color="text.secondary" display="block" mb={0.5}>
                    {sector.name}
                  </Typography>
                  <Typography variant="h6" fontWeight={700} sx={{ color }}>
                    {occupancyPercent}%
                  </Typography>
                  <Box sx={{ width: '100%', height: 4, backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: 2, mt: 1, overflow: 'hidden' }}>
                    <Box sx={{ width: `${occupancyPercent}%`, height: '100%', backgroundColor: color, borderRadius: 2, transition: 'width 0.5s' }} />
                  </Box>
                  <Typography variant="caption" color="text.secondary" display="block" mt={0.5}>
                    {sector.occupancy.toLocaleString()} / {sector.capacity.toLocaleString()}
                  </Typography>
                  {sector.activeAlerts > 0 && (
                    <Box sx={{ mt: 0.5, px: 1, py: 0.25, borderRadius: 1, backgroundColor: '#d32f2f20', display: 'inline-block' }}>
                      <Typography variant="caption" color="error" fontWeight={600}>
                        {sector.activeAlerts} alert{sector.activeAlerts > 1 ? 's' : ''}
                      </Typography>
                    </Box>
                  )}
                </Box>
              </Grid>
            );
          })}
        </Grid>
      </CardContent>
    </Card>
  );
}
