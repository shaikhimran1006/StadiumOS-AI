import { Box, Typography, Link } from '@mui/material';
import { SportsSoccer } from '@mui/icons-material';

export default function Footer() {
  return (
    <Box component="footer" sx={{ py: 2, px: 3, borderTop: '1px solid', borderColor: 'divider', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'background.paper' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <SportsSoccer sx={{ fontSize: 18, color: 'secondary.main' }} />
        <Typography variant="caption" color="text.secondary">
          StadiumOS AI &copy; {new Date().getFullYear()} FIFA World Cup 2026
        </Typography>
      </Box>
      <Box sx={{ display: 'flex', gap: 2 }}>
        <Link href="#" variant="caption" color="text.secondary" underline="hover">Privacy</Link>
        <Link href="#" variant="caption" color="text.secondary" underline="hover">Terms</Link>
        <Link href="#" variant="caption" color="text.secondary" underline="hover">Support</Link>
      </Box>
    </Box>
  );
}
