import { useState } from 'react';
import { Card, CardContent, Typography, Box, TextField, Button, List, ListItem, ListItemIcon, ListItemText, Divider, Chip } from '@mui/material';
import { DirectionsWalk, NavigationOutlined, AccessTime } from '@mui/icons-material';
import type { Direction } from '../../types';

interface NavigationPanelProps {
  direction: Direction | null;
  onGetDirections: (destination: { lat: number; lng: number }) => void;
  onClearRoute: () => void;
  loading?: boolean;
}

export default function NavigationPanel({ direction, onGetDirections, onClearRoute, loading }: NavigationPanelProps) {
  const [destinationInput, setDestinationInput] = useState('');

  const handleSearch = () => {
    if (!destinationInput.trim()) return;
    const coords = destinationInput.split(',').map((s) => parseFloat(s.trim()));
    if (coords.length === 2 && !isNaN(coords[0]) && !isNaN(coords[1])) {
      onGetDirections({ lat: coords[0], lng: coords[1] });
    }
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <NavigationOutlined sx={{ color: 'secondary.main' }} />
          <Typography variant="subtitle1" fontWeight={600}>Navigation</Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
          <TextField
            size="small"
            fullWidth
            placeholder="lat, lng (e.g. 32.7767, -96.7970)"
            value={destinationInput}
            onChange={(e) => setDestinationInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
          <Button variant="contained" color="secondary" onClick={handleSearch} disabled={loading} sx={{ minWidth: 'auto' }}>
            <DirectionsWalk />
          </Button>
        </Box>

        {direction && (
          <>
            <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
              <Chip icon={<DirectionsWalk sx={{ fontSize: 14 }} />} label={direction.distance} size="small" />
              <Chip icon={<AccessTime sx={{ fontSize: 14 }} />} label={direction.duration} size="small" />
            </Box>

            <Divider sx={{ mb: 1 }} />

            <List dense sx={{ maxHeight: 250, overflow: 'auto' }}>
              {direction.steps.map((step, idx) => (
                <ListItem key={idx} sx={{ py: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 28 }}>
                    <Typography variant="caption" color="secondary.main" fontWeight={700}>{idx + 1}</Typography>
                  </ListItemIcon>
                  <ListItemText
                    primary={<Typography variant="caption">{step.instruction}</Typography>}
                    secondary={<Typography variant="caption" color="text.secondary">{step.distance}</Typography>}
                  />
                </ListItem>
              ))}
            </List>

            <Button fullWidth variant="outlined" color="error" onClick={onClearRoute} sx={{ mt: 1 }}>
              Clear Route
            </Button>
          </>
        )}

        {!direction && (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <NavigationOutlined sx={{ fontSize: 40, color: 'text.secondary', opacity: 0.3 }} />
            <Typography variant="caption" color="text.secondary" display="block" mt={1}>
              Enter coordinates to get directions
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
}
