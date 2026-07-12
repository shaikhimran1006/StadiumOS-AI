import { Box, Typography, Chip } from '@mui/material';
import type { SectorStatus } from '../../types';

interface SectorOverlayProps {
  sectors: SectorStatus[];
  onSectorClick?: (sector: SectorStatus) => void;
}

const statusColors: Record<string, string> = {
  normal: '#2e7d32',
  warning: '#f9a825',
  critical: '#d32f2f',
  closed: '#616161',
};

export default function SectorOverlay({ sectors, onSectorClick }: SectorOverlayProps) {
  return (
    <Box
      sx={{
        position: 'absolute',
        bottom: 16,
        left: 16,
        backgroundColor: 'rgba(17, 22, 56, 0.95)',
        backdropFilter: 'blur(8px)',
        borderRadius: 2,
        border: '1px solid rgba(42, 47, 90, 0.5)',
        p: 1.5,
        maxHeight: 300,
        overflow: 'auto',
        minWidth: 200,
      }}
    >
      <Typography variant="caption" fontWeight={600} color="text.secondary" display="block" mb={1}>
        SECTORS
      </Typography>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
        {sectors.map((sector) => {
          const percent = sector.occupancyPercent || Math.round((sector.occupancy / sector.capacity) * 100);
          return (
            <Box
              key={sector.id}
              onClick={() => onSectorClick?.(sector)}
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                px: 1.5,
                py: 0.75,
                borderRadius: 1,
                cursor: 'pointer',
                '&:hover': { backgroundColor: 'rgba(255,255,255,0.06)' },
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Box sx={{ width: 8, height: 8, borderRadius: '50%', backgroundColor: statusColors[sector.status] }} />
                <Typography variant="caption" fontWeight={500}>{sector.name}</Typography>
              </Box>
              <Chip
                label={`${percent}%`}
                size="small"
                sx={{
                  height: 20,
                  fontSize: '0.65rem',
                  backgroundColor: `${statusColors[sector.status]}20`,
                  color: statusColors[sector.status],
                  fontWeight: 600,
                }}
              />
            </Box>
          );
        })}
      </Box>
    </Box>
  );
}
