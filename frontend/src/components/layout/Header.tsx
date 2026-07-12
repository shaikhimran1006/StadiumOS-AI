import { useState } from 'react';
import {
  AppBar, Toolbar, Typography, IconButton, Avatar, Menu, MenuItem, Box,
  Badge, Tooltip, InputBase, Select, MenuItem as SelectItem, FormControl,
} from '@mui/material';
import {
  Menu as MenuIcon, Notifications, Search, DarkMode, LightMode,
  AccountCircle, Logout, Settings,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useThemeContext } from '../../context/ThemeContext';

export default function Header({ onMenuClick }: { onMenuClick: () => void }) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const { mode, toggleMode } = useThemeContext();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [language, setLanguage] = useState('en');

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => setAnchorEl(event.currentTarget);
  const handleClose = () => setAnchorEl(null);

  return (
    <AppBar position="sticky" sx={{ zIndex: (t) => t.zIndex.drawer + 1 }}>
      <Toolbar>
        <IconButton color="inherit" edge="start" onClick={onMenuClick} sx={{ mr: 2, display: { md: 'none' } }}>
          <MenuIcon />
        </IconButton>

        <Typography variant="h6" noWrap sx={{ fontWeight: 700, mr: 2, display: { xs: 'none', sm: 'block' } }}>
          StadiumOS AI
        </Typography>

        <Box sx={{ flexGrow: 1, maxWidth: 400, mx: 2, display: { xs: 'none', md: 'flex' }, alignItems: 'center', backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: 2, px: 2, py: 0.5 }}>
          <Search sx={{ color: 'rgba(255,255,255,0.7)', mr: 1 }} />
          <InputBase placeholder="Search..." sx={{ color: 'inherit', flex: 1, fontSize: '0.875rem' }} />
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <FormControl size="small" sx={{ minWidth: 80 }}>
            <Select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              sx={{ color: 'white', fontSize: '0.8rem', '& .MuiOutlinedInput-notchedOutline': { borderColor: 'rgba(255,255,255,0.3)' } }}
            >
              <SelectItem value="en">EN</SelectItem>
              <SelectItem value="es">ES</SelectItem>
              <SelectItem value="fr">FR</SelectItem>
              <SelectItem value="ar">AR</SelectItem>
              <SelectItem value="pt">PT</SelectItem>
              <SelectItem value="zh">ZH</SelectItem>
            </Select>
          </FormControl>

          <Tooltip title={mode === 'dark' ? 'Light Mode' : 'Dark Mode'}>
            <IconButton color="inherit" onClick={toggleMode}>
              {mode === 'dark' ? <LightMode /> : <DarkMode />}
            </IconButton>
          </Tooltip>

          <Tooltip title="Notifications">
            <IconButton color="inherit">
              <Badge badgeContent={3} color="error">
                <Notifications />
              </Badge>
            </IconButton>
          </Tooltip>

          <Tooltip title={user?.name || 'Account'}>
            <IconButton onClick={handleMenu} sx={{ ml: 1 }}>
              <Avatar sx={{ width: 36, height: 36, bgcolor: 'secondary.main', color: 'black', fontWeight: 600 }}>
                {user?.name?.charAt(0) || 'U'}
              </Avatar>
            </IconButton>
          </Tooltip>
        </Box>

        <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleClose}
          PaperProps={{ sx: { mt: 1, minWidth: 180, bgcolor: 'background.paper' } }}>
          <Box sx={{ px: 2, py: 1 }}>
            <Typography variant="subtitle2">{user?.name}</Typography>
            <Typography variant="caption" color="text.secondary">{user?.email}</Typography>
          </Box>
          <MenuItem onClick={() => { handleClose(); navigate('/settings'); }}>
            <Settings sx={{ mr: 1 }} fontSize="small" /> Settings
          </MenuItem>
          <MenuItem onClick={() => { handleClose(); navigate('/settings'); }}>
            <AccountCircle sx={{ mr: 1 }} fontSize="small" /> Profile
          </MenuItem>
          <MenuItem onClick={() => { handleClose(); logout(); }} sx={{ color: 'error.main' }}>
            <Logout sx={{ mr: 1 }} fontSize="small" /> Logout
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  );
}
