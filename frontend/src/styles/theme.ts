import { createTheme, type ThemeOptions } from '@mui/material/styles';

const darkThemeOptions: ThemeOptions = {
  palette: {
    mode: 'dark',
    primary: { main: '#1a237e', light: '#283593', dark: '#0d1442', contrastText: '#ffffff' },
    secondary: { main: '#f9a825', light: '#fbc02d', dark: '#f57f17', contrastText: '#000000' },
    success: { main: '#2e7d32', light: '#43a047', dark: '#1b5e20' },
    error: { main: '#d32f2f', light: '#ef5350', dark: '#c62828' },
    warning: { main: '#ed6c02', light: '#ff9800', dark: '#e65100' },
    info: { main: '#0288d1', light: '#03a9f4', dark: '#01579b' },
    background: { default: '#0a0e27', paper: '#111638' },
    divider: 'rgba(42, 47, 90, 0.5)',
  },
  typography: {
    fontFamily: '"Inter", "Roboto", system-ui, sans-serif',
    h1: { fontWeight: 700 },
    h2: { fontWeight: 700 },
    h3: { fontWeight: 600 },
    h4: { fontWeight: 600 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
  },
  shape: { borderRadius: 12 },
  components: {
    MuiPaper: { styleOverrides: { root: { backgroundImage: 'none', background: '#111638' } } },
    MuiCard: { styleOverrides: { root: { background: '#1a1f4a', border: '1px solid rgba(42,47,90,0.5)' } } },
    MuiAppBar: { styleOverrides: { root: { background: 'linear-gradient(90deg, #1a237e 0%, #283593 100%)', boxShadow: 'none' } } },
    MuiDrawer: { styleOverrides: { paper: { background: '#111638', borderRight: '1px solid rgba(42,47,90,0.5)' } } },
    MuiButton: { styleOverrides: { root: { textTransform: 'none', borderRadius: 8 } } },
    MuiChip: { styleOverrides: { root: { borderRadius: 8 } } },
    MuiDialog: { styleOverrides: { paper: { background: '#111638', border: '1px solid rgba(42,47,90,0.5)' } } },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            '& fieldset': { borderColor: 'rgba(42,47,90,0.5)' },
            '&:hover fieldset': { borderColor: '#283593' },
            '&.Mui-focused fieldset': { borderColor: '#1a237e' },
          },
        },
      },
    },
  },
};

const lightThemeOptions: ThemeOptions = {
  palette: {
    mode: 'light',
    primary: { main: '#1a237e', light: '#283593', dark: '#0d1442', contrastText: '#ffffff' },
    secondary: { main: '#f9a825', light: '#fbc02d', dark: '#f57f17', contrastText: '#000000' },
    success: { main: '#2e7d32', light: '#43a047', dark: '#1b5e20' },
    background: { default: '#f5f5f5', paper: '#ffffff' },
    divider: 'rgba(0,0,0,0.08)',
  },
  typography: {
    fontFamily: '"Inter", "Roboto", system-ui, sans-serif',
  },
  shape: { borderRadius: 12 },
  components: {
    MuiButton: { styleOverrides: { root: { textTransform: 'none', borderRadius: 8 } } },
    MuiCard: { styleOverrides: { root: { border: '1px solid rgba(0,0,0,0.08)' } } },
  },
};

export function getTheme(mode: 'dark' | 'light') {
  return createTheme(mode === 'dark' ? darkThemeOptions : lightThemeOptions);
}
