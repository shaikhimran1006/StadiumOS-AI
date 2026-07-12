import { Box, Chip } from '@mui/material';
import { SmartToy, Security, HealthAndSafety, Build, Map, Event } from '@mui/icons-material';

const agentConfig: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
  security: { label: 'Security Agent', color: '#d32f2f', icon: <Security sx={{ fontSize: 14 }} /> },
  medical: { label: 'Medical Agent', color: '#2e7d32', icon: <HealthAndSafety sx={{ fontSize: 14 }} /> },
  operations: { label: 'Operations Agent', color: '#0288d1', icon: <Build sx={{ fontSize: '14px' }} /> },
  navigation: { label: 'Navigation Agent', color: '#f9a825', icon: <Map sx={{ fontSize: 14 }} /> },
  events: { label: 'Events Agent', color: '#9c27b0', icon: <Event sx={{ fontSize: 14 }} /> },
  general: { label: 'AI Assistant', color: '#1a237e', icon: <SmartToy sx={{ fontSize: 14 }} /> },
};

export default function AgentIndicator({ agent = 'general' }: { agent?: string }) {
  const config = agentConfig[agent] || agentConfig.general;

  return (
    <Chip
      icon={config.icon}
      label={config.label}
      size="small"
      sx={{
        height: 24,
        fontSize: '0.7rem',
        backgroundColor: `${config.color}20`,
        color: config.color,
        border: `1px solid ${config.color}40`,
        '& .MuiChip-icon': { color: config.color },
      }}
    />
  );
}
