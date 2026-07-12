import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Box, useMediaQuery, useTheme } from '@mui/material';
import Header from './Header';
import Sidebar from './Sidebar';

export default function AppLayout() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [drawerOpen, setDrawerOpen] = useState(!isMobile);

  return (
    <Box sx={{ display: 'flex', height: '100vh', overflow: 'hidden' }}>
      <Sidebar open={drawerOpen} onClose={() => setDrawerOpen(false)} isMobile={isMobile} />
      <Box sx={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
        <Header onMenuClick={() => setDrawerOpen(!drawerOpen)} />
        <Box component="main" sx={{ flex: 1, overflow: 'auto', p: 3, backgroundColor: 'background.default' }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
}
