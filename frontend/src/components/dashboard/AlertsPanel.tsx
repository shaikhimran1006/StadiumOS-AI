import { Card, CardContent, CardHeader, Box, Typography, IconButton, List, ListItem, ListItemIcon, ListItemText } from '@mui/material';
import { Warning, Error, Info, BugReport, LocalFireDepartment, Security, HealthAndSafety, Construction } from '@mui/icons-material';
import type { Alert } from '../../types';
import StatusBadge from '../common/StatusBadge';

const severityIcons: Record<string, React.ReactNode> = {
  critical: <Error sx={{ color: '#d32f2f' }} />,
  high: <Warning sx={{ color: '#ed6c02' }} />,
  medium: <Info sx={{ color: '#0288d1' }} />,
  low: <Info sx={{ color: '#2e7d32' }} />,
  info: <Info sx={{ color: '#9e9e9e' }} />,
};

const typeIcons: Record<string, React.ReactNode> = {
  security: <Security fontSize="small" />,
  medical: <HealthAndSafety fontSize="small" />,
  fire: <LocalFireDepartment fontSize="small" />,
  crowd: <BugReport fontSize="small" />,
  technical: <Construction fontSize="small" />,
};

interface AlertsPanelProps {
  alerts: Alert[];
  maxItems?: number;
  onAlertClick?: (alert: Alert) => void;
}

export default function AlertsPanel({ alerts, maxItems = 6, onAlertClick }: AlertsPanelProps) {
  const displayed = alerts.slice(0, maxItems);

  return (
    <Card sx={{ height: '100%' }}>
      <CardHeader
        title={<Typography variant="subtitle1" fontWeight={600}>Active Alerts</Typography>}
        subheader={`${alerts.length} active alerts`}
        action={<Typography variant="caption" color="secondary.main" sx={{ cursor: 'pointer' }}>View All</Typography>}
      />
      <CardContent sx={{ pt: 0, px: 0 }}>
        {displayed.length === 0 ? (
          <Box sx={{ px: 3, py: 4, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">No active alerts</Typography>
          </Box>
        ) : (
          <List disablePadding>
            {displayed.map((alert) => (
              <ListItem
                key={alert.id}
                onClick={() => onAlertClick?.(alert)}
                sx={{ px: 3, py: 1.5, cursor: 'pointer', '&:hover': { backgroundColor: 'action.hover' } }}
                secondaryAction={<StatusBadge status={alert.status} />}
              >
                <ListItemIcon sx={{ minWidth: 36 }}>
                  {severityIcons[alert.severity] || <Info />}
                </ListItemIcon>
                <ListItemText
                  primary={<Typography variant="body2" fontWeight={500} noWrap>{alert.title}</Typography>}
                  secondary={
                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center', mt: 0.5 }}>
                      {typeIcons[alert.type] && <Box sx={{ color: 'text.secondary', display: 'flex' }}>{typeIcons[alert.type]}</Box>}
                      <Typography variant="caption" color="text.secondary">
                        {alert.sector || 'General'} &middot; {new Date(alert.createdAt).toLocaleTimeString()}
                      </Typography>
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        )}
      </CardContent>
    </Card>
  );
}
