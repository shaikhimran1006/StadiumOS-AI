import { Card, CardContent, CardHeader, Typography, List, ListItem, ListItemIcon, ListItemText, Box } from '@mui/material';
import { ReportProblem, Assignment, Build, Warning } from '@mui/icons-material';
import type { Incident } from '../../types';
import StatusBadge from '../common/StatusBadge';

const priorityIcons: Record<string, React.ReactNode> = {
  critical: <Warning sx={{ color: '#d32f2f' }} />,
  high: <ReportProblem sx={{ color: '#ed6c02' }} />,
  medium: <Assignment sx={{ color: '#0288d1' }} />,
  low: <Build sx={{ color: '#2e7d32' }} />,
};

interface IncidentsPanelProps {
  incidents: Incident[];
  maxItems?: number;
  onIncidentClick?: (incident: Incident) => void;
}

export default function IncidentsPanel({ incidents, maxItems = 6, onIncidentClick }: IncidentsPanelProps) {
  const displayed = incidents.slice(0, maxItems);

  return (
    <Card sx={{ height: '100%' }}>
      <CardHeader
        title={<Typography variant="subtitle1" fontWeight={600}>Active Incidents</Typography>}
        subheader={`${incidents.length} active incidents`}
        action={<Typography variant="caption" color="secondary.main" sx={{ cursor: 'pointer' }}>View All</Typography>}
      />
      <CardContent sx={{ pt: 0, px: 0 }}>
        {displayed.length === 0 ? (
          <Box sx={{ px: 3, py: 4, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">No active incidents</Typography>
          </Box>
        ) : (
          <List disablePadding>
            {displayed.map((incident) => (
              <ListItem
                key={incident.id}
                onClick={() => onIncidentClick?.(incident)}
                sx={{ px: 3, py: 1.5, cursor: 'pointer', '&:hover': { backgroundColor: 'action.hover' } }}
                secondaryAction={<StatusBadge status={incident.status} />}
              >
                <ListItemIcon sx={{ minWidth: 36 }}>
                  {priorityIcons[incident.priority] || <Assignment />}
                </ListItemIcon>
                <ListItemText
                  primary={<Typography variant="body2" fontWeight={500} noWrap>{incident.title}</Typography>}
                  secondary={
                    <Typography variant="caption" color="text.secondary">
                      {incident.category} &middot; {incident.sector || 'General'} &middot; {new Date(incident.createdAt).toLocaleTimeString()}
                    </Typography>
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
