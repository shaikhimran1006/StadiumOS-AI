import { useState } from 'react';
import {
  Box, Typography, Button, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, IconButton, Chip, Dialog, DialogTitle, DialogContent, DialogActions, TextField,
  FormControl, InputLabel, Select, MenuItem, TablePagination,
} from '@mui/material';
import { Add, Edit, Delete } from '@mui/icons-material';
import { useIncidents } from '../hooks/useIncidents';
import StatusBadge from '../components/common/StatusBadge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ConfirmDialog from '../components/common/ConfirmDialog';
import type { Incident, IncidentCategory, IncidentStatus } from '../types';

const priorityColors: Record<string, string> = {
  critical: '#d32f2f', high: '#ed6c02', medium: '#0288d1', low: '#2e7d32',
};

export default function IncidentsPage() {
  const { incidents, total, page, setPage, loading, createIncident, resolveIncident, deleteIncident } = useIncidents();
  const [createOpen, setCreateOpen] = useState(false);
  const [resolveOpen, setResolveOpen] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [resolution, setResolution] = useState('');
  const [newIncident, setNewIncident] = useState({
    title: '', description: '', category: 'other' as IncidentCategory,
    priority: 'medium' as string, sector: '',
  });

  const handleCreate = async () => {
    await createIncident({ ...newIncident } as Partial<Incident>);
    setCreateOpen(false);
    setNewIncident({ title: '', description: '', category: 'other', priority: 'medium', sector: '' });
  };

  const handleResolve = async () => {
    if (selectedIncident) {
      await resolveIncident(selectedIncident.id, resolution);
      setResolveOpen(false);
      setResolution('');
      setSelectedIncident(null);
    }
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" fontWeight={700}>Incidents</Typography>
          <Typography variant="body2" color="text.secondary">Track and manage stadium incidents</Typography>
        </Box>
        <Button variant="contained" color="secondary" startIcon={<Add />} onClick={() => setCreateOpen(true)}>
          Report Incident
        </Button>
      </Box>

      {loading ? (
        <LoadingSpinner message="Loading incidents..." />
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Priority</TableCell>
                <TableCell>Title</TableCell>
                <TableCell>Category</TableCell>
                <TableCell>Sector</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Reported</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {incidents.map((incident) => (
                <TableRow key={incident.id} hover>
                  <TableCell>
                    <Chip label={incident.priority} size="small" sx={{ backgroundColor: `${priorityColors[incident.priority]}20`, color: priorityColors[incident.priority], fontWeight: 600, textTransform: 'capitalize' }} />
                  </TableCell>
                  <TableCell><Typography variant="body2" fontWeight={500}>{incident.title}</Typography></TableCell>
                  <TableCell><Typography variant="body2" sx={{ textTransform: 'capitalize' }}>{incident.category}</Typography></TableCell>
                  <TableCell><Typography variant="body2">{incident.sector || '-'}</Typography></TableCell>
                  <TableCell><StatusBadge status={incident.status} /></TableCell>
                  <TableCell><Typography variant="caption">{new Date(incident.createdAt).toLocaleString()}</Typography></TableCell>
                  <TableCell align="right">
                    {incident.status !== 'resolved' && incident.status !== 'closed' && (
                      <IconButton size="small" onClick={() => { setSelectedIncident(incident); setResolveOpen(true); }}>
                        <Edit fontSize="small" color="success" />
                      </IconButton>
                    )}
                    <IconButton size="small" onClick={() => setDeleteConfirm(incident.id)}>
                      <Delete fontSize="small" color="error" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <TablePagination component="div" count={total} page={page - 1} onPageChange={(_, p) => setPage(p + 1)} rowsPerPage={20} rowsPerPageOptions={[20]} />
        </TableContainer>
      )}

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle fontWeight={600}>Report New Incident</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '16px !important' }}>
          <TextField label="Title" fullWidth value={newIncident.title} onChange={(e) => setNewIncident({ ...newIncident, title: e.target.value })} />
          <TextField label="Description" fullWidth multiline rows={3} value={newIncident.description} onChange={(e) => setNewIncident({ ...newIncident, description: e.target.value })} />
          <FormControl fullWidth>
            <InputLabel>Category</InputLabel>
            <Select value={newIncident.category} label="Category" onChange={(e) => setNewIncident({ ...newIncident, category: e.target.value as IncidentCategory })}>
              {['security', 'medical', 'fire', 'structural', 'crowd', 'equipment', 'weather', 'other'].map((c) => (
                <MenuItem key={c} value={c} sx={{ textTransform: 'capitalize' }}>{c}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl fullWidth>
            <InputLabel>Priority</InputLabel>
            <Select value={newIncident.priority} label="Priority" onChange={(e) => setNewIncident({ ...newIncident, priority: e.target.value })}>
              {['critical', 'high', 'medium', 'low'].map((p) => (
                <MenuItem key={p} value={p} sx={{ textTransform: 'capitalize' }}>{p}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField label="Sector" fullWidth value={newIncident.sector} onChange={(e) => setNewIncident({ ...newIncident, sector: e.target.value })} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button variant="contained" color="secondary" onClick={handleCreate} disabled={!newIncident.title}>Report</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={resolveOpen} onClose={() => setResolveOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle fontWeight={600}>Resolve Incident</DialogTitle>
        <DialogContent>
          <TextField fullWidth multiline rows={3} label="Resolution notes" value={resolution} onChange={(e) => setResolution(e.target.value)} sx={{ mt: 1 }} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResolveOpen(false)}>Cancel</Button>
          <Button variant="contained" color="success" onClick={handleResolve}>Resolve</Button>
        </DialogActions>
      </Dialog>

      <ConfirmDialog open={!!deleteConfirm} title="Delete Incident" message="Are you sure you want to delete this incident?" confirmText="Delete" severity="error" onConfirm={() => deleteConfirm && deleteIncident(deleteConfirm).then(() => setDeleteConfirm(null))} onCancel={() => setDeleteConfirm(null)} />
    </Box>
  );
}
