import { useState } from 'react';
import {
  Box, Typography, Card, CardContent, Switch, FormControlLabel, Select, MenuItem,
  FormControl, InputLabel, Button, Divider, Avatar, TextField, Grid,
} from '@mui/material';
import { DarkMode, Language, Notifications, Person, Save } from '@mui/icons-material';
import { useAuth } from '../hooks/useAuth';
import { useThemeContext } from '../context/ThemeContext';

export default function SettingsPage() {
  const { user } = useAuth();
  const { mode, toggleMode } = useThemeContext();
  const [language, setLanguage] = useState('en');
  const [notifications, setNotifications] = useState({ email: true, push: true, sms: false });
  const [profile, setProfile] = useState({ name: user?.name || '', email: user?.email || '' });

  const handleSave = () => {
    localStorage.setItem('stadiumos_language', language);
  };

  return (
    <Box>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" fontWeight={700}>Settings</Typography>
        <Typography variant="body2" color="text.secondary">Manage your preferences and account settings</Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <Person sx={{ color: 'secondary.main' }} />
                <Typography variant="h6" fontWeight={600}>Profile</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
                <Avatar sx={{ width: 64, height: 64, bgcolor: 'secondary.main', color: 'black', fontSize: 24 }}>
                  {user?.name?.charAt(0) || 'U'}
                </Avatar>
                <Box>
                  <Typography fontWeight={600}>{user?.name || 'User'}</Typography>
                  <Typography variant="body2" color="text.secondary">{user?.role || 'operator'}</Typography>
                </Box>
              </Box>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <TextField label="Full Name" fullWidth size="small" value={profile.name} onChange={(e) => setProfile({ ...profile, name: e.target.value })} />
                <TextField label="Email" fullWidth size="small" value={profile.email} onChange={(e) => setProfile({ ...profile, email: e.target.value })} disabled />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <DarkMode sx={{ color: 'secondary.main' }} />
                <Typography variant="h6" fontWeight={600}>Appearance</Typography>
              </Box>
              <FormControlLabel
                control={<Switch checked={mode === 'dark'} onChange={toggleMode} color="secondary" />}
                label={<Typography variant="body2">Dark Mode</Typography>}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <Language sx={{ color: 'secondary.main' }} />
                <Typography variant="h6" fontWeight={600}>Language & Region</Typography>
              </Box>
              <FormControl fullWidth size="small">
                <InputLabel>Language</InputLabel>
                <Select value={language} label="Language" onChange={(e) => setLanguage(e.target.value)}>
                  <MenuItem value="en">English</MenuItem>
                  <MenuItem value="es">Español</MenuItem>
                  <MenuItem value="fr">Français</MenuItem>
                  <MenuItem value="de">Deutsch</MenuItem>
                  <MenuItem value="ar">العربية</MenuItem>
                  <MenuItem value="pt">Português</MenuItem>
                  <MenuItem value="zh">中文</MenuItem>
                  <MenuItem value="ja">日本語</MenuItem>
                </Select>
              </FormControl>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                <Notifications sx={{ color: 'secondary.main' }} />
                <Typography variant="h6" fontWeight={600}>Notifications</Typography>
              </Box>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <FormControlLabel
                  control={<Switch checked={notifications.email} onChange={(e) => setNotifications({ ...notifications, email: e.target.checked })} color="secondary" />}
                  label={<Typography variant="body2">Email Notifications</Typography>}
                />
                <FormControlLabel
                  control={<Switch checked={notifications.push} onChange={(e) => setNotifications({ ...notifications, push: e.target.checked })} color="secondary" />}
                  label={<Typography variant="body2">Push Notifications</Typography>}
                />
                <FormControlLabel
                  control={<Switch checked={notifications.sms} onChange={(e) => setNotifications({ ...notifications, sms: e.target.checked })} color="secondary" />}
                  label={<Typography variant="body2">SMS Alerts</Typography>}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
        <Button variant="contained" color="secondary" startIcon={<Save />} onClick={handleSave} size="large">
          Save Settings
        </Button>
      </Box>
    </Box>
  );
}
