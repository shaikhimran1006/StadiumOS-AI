import { useState } from 'react';
import {
  Box, Typography, Button, Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Paper, IconButton, Chip, Dialog, DialogTitle, DialogContent, DialogActions, TextField,
  FormControl, InputLabel, Select, MenuItem, TablePagination,
} from '@mui/material';
import { Add, Warning, Edit, Delete, CheckCircle, ArrowUpward } from '@mui/icons-material';
import { useAlerts } from '../hooks/useAlerts';
import StatusBadge from '../components/common/StatusBadge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ConfirmDialog from '../components/common/ConfirmDialog';
import type { Alert, AlertType, AlertSeverity } from '../types';

const severityColors: Record<string, string> = {
  critical: '#d32f2f',
  high: '#ed6c02',
  medium: '#0288d1',
  low: '#2e7d32',
  info: '#9e9e9e',
};

export default function AlertsPage() {
  const { alerts, total, page, setPage, loading, createAlert, acknowledgeAlert, resolveAlert, escalateAlert, deleteAlert } = useAlerts();
  const [createOpen, setCreateOpen] = useState(false);
  const [resolveOpen, setResolveOpen] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [newAlert, setNewAlert] = useState({ title: '', description: '', type: 'general' as AlertType, severity: 'medium' as AlertSeverity, sector: '' });
  const [resolution, setResolution] = useState('');

  const handleCreate = async () => {
    await createAlert({ ...newAlert } as Partial<Alert>);
    setCreateOpen(false);
    setNewAlert({ title: '', description: '', type: 'general', severity: 'medium', sector: '' });
  };

  const handleResolve = async () => {
    if (selectedAlert) {
      await resolveAlert(selectedAlert.id, resolution);
      setResolveOpen(false);
      setResolution('');
      setSelectedAlert(null);
    }
  };

  const handleDelete = async (id: string) => {
    await deleteAlert(id);
    setDeleteConfirm(null);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" fontWeight={700}>Alerts</Typography>
          <Typography variant="body2" color="text.secondary">Manage and monitor stadium alerts</Typography>
        </Box>
        <Button variant="contained" color="secondary" startIcon={<Add />} onClick={() => setCreateOpen(true)}>
          New Alert
        </Button>
      </Box>

      {loading ? (
        <LoadingSpinner message="Loading alerts..." />
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Severity</TableCell>
                <TableCell>Title</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Sector</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Created</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {alerts.map((alert) => (
                <TableRow key={alert.id} hover>
                  <TableCell>
                    <Chip
                      label={alert.severity}
                      size="small"
                      sx={{ backgroundColor: `${severityColors[alert.severity]}20`, color: severityColors[alert.severity], fontWeight: 600, textTransform: 'capitalize' }}
                    />
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Warning sx={{ fontSize: 16, color: severityColors[alert.severity] }} />
                      <Typography variant="body2" fontWeight={500}>{alert.title}</Typography>
                    </Box>
                  </TableCell>
                  <TableCell><Typography variant="body2" sx={{ textTransform: 'capitalize' }}>{alert.type}</Typography></TableCell>
                  <TableCell><Typography variant="body2">{alert.sector || '-'}</Typography></TableCell>
                  <TableCell><StatusBadge status={alert.status} /></TableCell>
                  <TableCell><Typography variant="caption">{new Date(alert.createdAt).toLocaleString()}</Typography></TableCell>
                  <TableCell align="right">
                    {alert.status === 'active' && (
                      <IconButton size="small" onClick={() => acknowledgeAlert(alert.id)} title="Acknowledge">
                        <CheckCircle fontSize="small" color="info" />
                      </IconButton>
                    )}
                    {alert.status !== 'resolved' && (
                      <IconButton size="small" onClick={() => { setSelectedAlert(alert); setResolveOpen(true); }} title="Resolve">
                        <CheckCircle fontSize="small" color="success" />
                      </IconButton>
                    )}
                    {alert.status === 'active' && (
                      <IconButton size="small" onClick={() => escalateAlert(alert.id, 'Manual escalation')} title="Escalate">
                        <ArrowUpward fontSize="small" color="error" />
                      </IconButton>
                    )}
                    <IconButton size="small" onClick={() => setDeleteConfirm(alert.id)} title="Delete">
                      <Delete fontSize="small" color="error" />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
          <TablePagination
            component="div"
            count={total}
            page={page - 1}
            onPageChange={(_, p) => setPage(p + 1)}
            rowsPerPage={20}
            rowsPerPageOptions={[20]}
          />
        </TableContainer>
      )}

      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle fontWeight={600}>Create New Alert</DialogTitle>
        <DialogContent sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: '16px !important' }}>
          <TextField label="Title" fullWidth value={newAlert.title} onChange={(e) => setNewAlert({ ...newAlert, title: e.target.value })} />
          <TextField label="Description" fullWidth multiline rows={3} value={newAlert.description} onChange={(e) => setNewAlert({ ...newAlert, description: e.target.value })} />
          <FormControl fullWidth>
            <InputLabel>Type</InputLabel>
            <Select value={newAlert.type} label="Type" onChange={(e) => setNewAlert({ ...newAlert, type: e.target.value as AlertType })}>
              {['security', 'medical', 'fire', 'weather', 'crowd', 'technical', 'vip', 'general'].map((t) => (
                <MenuItem key={t} value={t} sx={{ textTransform: 'capitalize' }}>{t}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl fullWidth>
            <InputLabel>Severity</InputLabel>
            <Select value={newAlert.severity} label="Severity" onChange={(e) => setNewAlert({ ...newAlert, severity: e.target.value as AlertSeverity })}>
              {['critical', 'high', 'medium', 'low', 'info'].map((s) => (
                <MenuItem key={s} value={s} sx={{ textTransform: 'capitalize' }}>{s}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <TextField label="Sector" fullWidth value={newAlert.sector} onChange={(e) => setNewAlert({ ...newAlert, sector: e.target.value })} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancel</Button>
          <Button variant="contained" color="secondary" onClick={handleCreate} disabled={!newAlert.title}>Create</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={resolveOpen} onClose={() => setResolveOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle fontWeight={600}>Resolve Alert</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth multiline rows={3} label="Resolution notes"
            value={resolution} onChange={(e) => setResolution(e.target.value)}
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setResolveOpen(false)}>Cancel</Button>
          <Button variant="contained" color="success" onClick={handleResolve}>Resolve</Button>
        </DialogActions>
      </Dialog>

      <ConfirmDialog
        open={!!deleteConfirm}
        title="Delete Alert"
        message="Are you sure you want to delete this alert? This action cannot be undone."
        confirmText="Delete"
        severity="error"
        onConfirm={() => deleteConfirm && handleDelete(deleteConfirm)}
        onCancel={() => setDeleteConfirm(null)}
      />
    </Box>
  );
}
