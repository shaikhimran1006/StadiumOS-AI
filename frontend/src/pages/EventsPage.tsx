import { useState, useEffect } from 'react';
import {
  Box, Typography, Button, Grid, Card, CardContent, CardMedia, CardActions,
  Chip, Dialog, DialogTitle, DialogContent, DialogActions, TextField,
  FormControl, InputLabel, Select, MenuItem,
} from '@mui/material';
import { Add, CalendarMonth, People, LocationOn } from '@mui/icons-material';
import { eventsApi } from '../services/api/events';
import LoadingSpinner from '../components/common/LoadingSpinner';
import type { Event } from '../types';

const statusColors: Record<string, 'success' | 'warning' | 'info' | 'default'> = {
  live: 'success', upcoming: 'info', completed: 'default', cancelled: 'default',
};

export default function EventsPage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [filter, setFilter] = useState('all');
  const [newEvent, setNewEvent] = useState({
    name: '', description: '', date: '', type: 'match' as Event['type'],
    venue: '', expectedAttendance: 0, teamHome: '', teamAway: '',
  });

  useEffect(() => {
    loadEvents();
  }, []);

  const loadEvents = async () => {
    try {
      setLoading(true);
      const response = await eventsApi.list({ pageSize: 50 });
      setEvents(response.data);
    } catch { /* ignore */ } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      await eventsApi.create({
        name: newEvent.name,
        description: newEvent.description,
        date: newEvent.date,
        type: newEvent.type,
        venue: newEvent.venue,
        expectedAttendance: newEvent.expectedAttendance,
        teams: newEvent.teamHome ? { home: newEvent.teamHome, away: newEvent.teamAway } : undefined,
        status: 'upcoming',
      });
      setCreateOpen(false);
      loadEvents();
    } catch { /* ignore */ }
  };

  const filtered = filter === 'all' ? events : events.filter((e) => e.status === filter);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" fontWeight={700}>Events</Typography>
          <Typography variant="body2" color="text.secondary">Manage stadium events and matches</Typography>
        </Box>
        <Button variant="contained" color="secondary" startIcon={<Add />} onClick={() => setCreateOpen(true)}>
          New Event
        </Button>
      </Box>

      <Box sx={{ display: 'flex', gap: 1, mb: 3 }}>
        {['all', 'live', 'upcoming', 'completed'].map((f) => (
          <Chip key={f} label={f.charAt(0).toUpperCase() + f.slice(1)} onClick={() => setFilter(f)} variant={filter === f ? 'filled' : 'outlined'} color={filter === f ? 'secondary' : 'default'} sx={{ textTransform: 'capitalize' }} />
        ))}
      </Box>

      {loading ? (
        <LoadingSpinner message="Loading events..." />
      ) : (
        <Grid container spacing={3}>
          {filtered.map((event) => (
            <Grid item xs={12} sm={6} md={4} key={event.id}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardMedia
                  component="div"
                  sx={{ height: 140, background: event.type === 'match' ? 'linear-gradient(135deg, #1a237e 0%, #283593 100%)' : 'linear-gradient(135deg, #9c27b0 0%, #7b1fa2 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
                >
                  <Typography variant="h3" fontWeight={700} sx={{ opacity: 0.3 }}>
                    {event.type === 'match' ? '⚽' : event.type === 'concert' ? '🎵' : '📋'}
                  </Typography>
                </CardMedia>
                <CardContent sx={{ flex: 1 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                    <Typography variant="h6" fontWeight={600} noWrap>{event.name}</Typography>
                    <Chip label={event.status} size="small" color={statusColors[event.status] || 'default'} sx={{ textTransform: 'capitalize' }} />
                  </Box>
                  {event.teams && (
                    <Typography variant="body2" color="secondary.main" fontWeight={600} mb={1}>
                      {event.teams.home} vs {event.teams.away}
                    </Typography>
                  )}
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <CalendarMonth sx={{ fontSize: 14, color: 'text.secondary' }} />
                      <Typography variant="caption" color="text.secondary">{new Date(event.date).toLocaleString()}</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <LocationOn sx={{ fontSize: 14, color: 'text.secondary' }} />
                      <Typography variant="caption" color="text.secondary">{event.venue}</Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      <People sx={{ fontSize: 14, color: 'text.secondary' }} />
                      <Typography variant="caption" color="text.secondary">{event.expectedAttendance.toLocaleString()} expected</Typography>
                    </Box>
                  </Box>
                </CardContent>
                <CardActions sx={{ px: 2, pb: 2 }}>
                  <Button size="small" variant="outlined">View Details</Button>
                  {event.status === 'live' && <Chip label="LIVE" size="small" color="error" sx={{ fontWeight: 700, animation: 'pulse 2s infinite' }} />}
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle fontWeight={600}>Create New Event</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '16px !important' }}>
          <TextField label="Event Name" fullWidth value={newEvent.name} onChange={(e) => setNewEvent({ ...newEvent, name: e.target.value })} />
          <TextField label="Description" fullWidth multiline rows={2} value={newEvent.description} onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })} />
          <TextField label="Date & Time" type="datetime-local" fullWidth InputLabelProps={{ shrink: true }} value={newEvent.date} onChange={(e) => setNewEvent({ ...newEvent, date: e.target.value })} />
          <FormControl fullWidth>
            <InputLabel>Type</InputLabel>
            <Select value={newEvent.type} label="Type" onChange={(e) => setNewEvent({ ...newEvent, type: e.target.value as Event['type'] })}>
              <MenuItem value="match">Match</MenuItem>
              <MenuItem value="concert">Concert</MenuItem>
              <MenuItem value="conference">Conference</MenuItem>
              <MenuItem value="other">Other</MenuItem>
            </Select>
          </FormControl>
          <TextField label="Venue" fullWidth value={newEvent.venue} onChange={(e) => setNewEvent({ ...newEvent, venue: e.target.value })} />
          <TextField label="Expected Attendance" type="number" fullWidth value={newEvent.expectedAttendance || ''} onChange={(e) => setNewEvent({ ...newEvent, expectedAttendance: parseInt(e.target.value) || 0 })} />
          {newEvent.type === 'match' && (
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField label="Home Team" fullWidth value={newEvent.teamHome} onChange={(e) => setNewEvent({ ...newEvent, teamHome: e.target.value })} />
              <TextField label="Away Team" fullWidth value={newEvent.teamAway} onChange={(e) => setNewEvent({ ...newEvent, teamAway: e.target.value })} />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button variant="contained" color="secondary" onClick={handleCreate} disabled={!newEvent.name}>Create</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
