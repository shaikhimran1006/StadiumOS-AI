import { useState } from 'react';
import { Box, Paper, Typography, Button, TextField, Divider, Alert, CircularProgress } from '@mui/material';
import { SportsSoccer, Google } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';

export default function LoginPage() {
  const navigate = useNavigate();
  const { loginWithGoogle, loading } = useAuth();
  const [error, setError] = useState<string | null>(null);

  const handleGoogleLogin = async () => {
    try {
      setError(null);
      await loginWithGoogle();
      navigate('/dashboard');
    } catch {
      setError('Google authentication failed. Please try again.');
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(135deg, #0a0e27 0%, #1a237e 50%, #0d1442 100%)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <Box sx={{ position: 'absolute', inset: 0, opacity: 0.1 }}>
        {Array.from({ length: 20 }).map((_, i) => (
          <Box
            key={i}
            sx={{
              position: 'absolute',
              width: Math.random() * 200 + 50,
              height: Math.random() * 200 + 50,
              borderRadius: '50%',
              border: '1px solid rgba(249, 168, 37, 0.3)',
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              transform: 'translate(-50%, -50%)',
            }}
          />
        ))}
      </Box>

      <Paper
        elevation={24}
        sx={{
          width: '100%',
          maxWidth: 440,
          mx: 2,
          p: 4,
          borderRadius: 3,
          backgroundColor: 'rgba(17, 22, 56, 0.95)',
          backdropFilter: 'blur(20px)',
          border: '1px solid rgba(42, 47, 90, 0.5)',
          position: 'relative',
          zIndex: 1,
        }}
      >
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <Box sx={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: 72, height: 72, borderRadius: '50%', backgroundColor: 'rgba(249,168,37,0.15)', mb: 2 }}>
            <SportsSoccer sx={{ fontSize: 40, color: 'secondary.main' }} />
          </Box>
          <Typography variant="h4" fontWeight={700}>StadiumOS AI</Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            FIFA World Cup 2026 Operations Platform
          </Typography>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>
        )}

        <Button
          fullWidth
          variant="contained"
          size="large"
          startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <Google />}
          onClick={handleGoogleLogin}
          disabled={loading}
          sx={{
            py: 1.5,
            backgroundColor: '#4285f4',
            '&:hover': { backgroundColor: '#357ae8' },
            fontSize: '1rem',
            fontWeight: 600,
          }}
        >
          Sign in with Google
        </Button>

        <Divider sx={{ my: 3 }}>
          <Typography variant="caption" color="text.secondary">or</Typography>
        </Divider>

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField fullWidth label="Email" placeholder="operator@stadium.com" size="small" />
          <TextField fullWidth label="Password" type="password" placeholder="Enter your password" size="small" />
          <Button fullWidth variant="outlined" size="large" sx={{ py: 1.5, fontWeight: 600 }}>
            Sign In
          </Button>
        </Box>

        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', textAlign: 'center', mt: 3 }}>
          Authorized personnel only. Contact admin for access.
        </Typography>
      </Paper>
    </Box>
  );
}
