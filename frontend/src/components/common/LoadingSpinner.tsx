import { Box, CircularProgress, Typography } from '@mui/material';

interface LoadingSpinnerProps {
  size?: number;
  message?: string;
  fullScreen?: boolean;
}

export default function LoadingSpinner({ size = 40, message, fullScreen = false }: LoadingSpinnerProps) {
  const content = (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2 }}>
      <CircularProgress size={size} sx={{ color: 'secondary.main' }} />
      {message && <Typography variant="body2" color="text.secondary">{message}</Typography>}
    </Box>
  );

  if (fullScreen) {
    return (
      <Box sx={{ position: 'fixed', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(10,14,39,0.8)', zIndex: 9999 }}>
        {content}
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', py: 8 }}>
      {content}
    </Box>
  );
}
