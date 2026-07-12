import { useNavigate, useLocation } from 'react-router-dom';
import {
  Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Box,
  Typography, Divider, Avatar, Chip,
} from '@mui/material';
import {
  Dashboard, Chat, Warning, ReportProblem, Event, Map, Analytics,
  Settings, SportsSoccer,
} from '@mui/icons-material';
import { useAuth } from '../../hooks/useAuth';

const DRAWER_WIDTH = 260;

const navItems = [
  { label: 'Dashboard', path: '/dashboard', icon: <Dashboard /> },
  { label: 'AI Chat', path: '/chat', icon: <Chat /> },
  { label: 'Alerts', path: '/alerts', icon: <Warning /> },
  { label: 'Incidents', path: '/incidents', icon: <ReportProblem /> },
  { label: 'Events', path: '/events', icon: <Event /> },
  { label: 'Maps', path: '/maps', icon: <Map /> },
  { label: 'Analytics', path: '/analytics', icon: <Analytics /> },
  { label: 'Settings', path: '/settings', icon: <Settings /> },
];

interface SidebarProps {
  open: boolean;
  onClose: () => void;
  isMobile: boolean;
}

export default function Sidebar({ open, onClose, isMobile }: SidebarProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  const drawerContent = (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 1.5 }}>
        <Avatar sx={{ bgcolor: 'secondary.main', color: 'black', width: 42, height: 42 }}>
          <SportsSoccer />
        </Avatar>
        <Box>
          <Typography variant="subtitle1" fontWeight={700} lineHeight={1.2}>StadiumOS</Typography>
          <Typography variant="caption" color="secondary.main" fontWeight={500}>FIFA World Cup 2026</Typography>
        </Box>
      </Box>

      <Divider sx={{ borderColor: 'divider' }} />

      <List sx={{ flex: 1, px: 1, py: 1 }}>
        {navItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <ListItem key={item.path} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                onClick={() => { navigate(item.path); if (isMobile) onClose(); }}
                sx={{
                  borderRadius: 2,
                  py: 1.2,
                  px: 2,
                  backgroundColor: isActive ? 'rgba(249,168,37,0.12)' : 'transparent',
                  '&:hover': { backgroundColor: 'rgba(255,255,255,0.06)' },
                  ...(isActive && { borderLeft: '3px solid', borderLeftColor: 'secondary.main' }),
                }}
              >
                <ListItemIcon sx={{ color: isActive ? 'secondary.main' : 'text.secondary', minWidth: 40 }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.label}
                  primaryTypographyProps={{ fontSize: '0.875rem', fontWeight: isActive ? 600 : 400, color: isActive ? 'white' : 'text.secondary' }}
                />
                {item.label === 'Alerts' && (
                  <Chip label="3" size="small" color="error" sx={{ height: 20, fontSize: '0.7rem' }} />
                )}
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>

      <Divider sx={{ borderColor: 'divider' }} />

      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 1.5 }}>
        <Avatar sx={{ width: 36, height: 36, bgcolor: 'primary.light' }}>
          {user?.name?.charAt(0) || 'U'}
        </Avatar>
        <Box sx={{ overflow: 'hidden' }}>
          <Typography variant="body2" fontWeight={500} noWrap>{user?.name || 'User'}</Typography>
          <Typography variant="caption" color="text.secondary" noWrap sx={{ textTransform: 'capitalize' }}>
            {user?.role || 'operator'}
          </Typography>
        </Box>
      </Box>
    </Box>
  );

  if (isMobile) {
    return (
      <Drawer
        variant="temporary"
        open={open}
        onClose={onClose}
        ModalProps={{ keepMounted: true }}
        sx={{ '& .MuiDrawer-paper': { width: DRAWER_WIDTH, boxSizing: 'border-box' } }}
      >
        {drawerContent}
      </Drawer>
    );
  }

  return (
    <Drawer
      variant="persistent"
      open={open}
      sx={{
        width: open ? DRAWER_WIDTH : 0,
        flexShrink: 0,
        '& .MuiDrawer-paper': { width: DRAWER_WIDTH, boxSizing: 'border-box', transition: 'width 0.3s' },
      }}
    >
      {drawerContent}
    </Drawer>
  );
}
