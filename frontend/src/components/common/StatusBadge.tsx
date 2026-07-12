import { Chip, type ChipProps } from '@mui/material';

interface StatusBadgeProps {
  status: string;
  size?: ChipProps['size'];
}

const statusColors: Record<string, ChipProps['color']> = {
  active: 'error',
  critical: 'error',
  high: 'error',
  escalated: 'error',
  reported: 'warning',
  warning: 'warning',
  medium: 'warning',
  investigating: 'info',
  in_progress: 'info',
  acknowledged: 'info',
  resolved: 'success',
  normal: 'success',
  low: 'success',
  closed: 'default',
  info: 'info',
};

export default function StatusBadge({ status, size = 'small' }: StatusBadgeProps) {
  return (
    <Chip
      label={status.replace(/_/g, ' ')}
      color={statusColors[status] || 'default'}
      size={size}
      sx={{ textTransform: 'capitalize', fontWeight: 500 }}
    />
  );
}
