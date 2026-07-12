import { Box, IconButton, Tooltip, Typography } from '@mui/material';
import { Mic, MicOff } from '@mui/icons-material';

interface VoiceInputProps {
  isListening: boolean;
  onToggle: () => void;
  interimTranscript?: string;
}

export default function VoiceInput({ isListening, onToggle, interimTranscript }: VoiceInputProps) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
      <Tooltip title={isListening ? 'Stop recording' : 'Start voice input'}>
        <IconButton
          onClick={onToggle}
          sx={{
            width: 48,
            height: 48,
            backgroundColor: isListening ? '#d32f2f' : 'background.paper',
            color: isListening ? 'white' : 'text.secondary',
            border: '1px solid',
            borderColor: isListening ? '#d32f2f' : 'divider',
            animation: isListening ? 'pulse 1.5s infinite' : 'none',
            '&:hover': { backgroundColor: isListening ? '#c62828' : 'action.hover' },
          }}
        >
          {isListening ? <Mic /> : <MicOff />}
        </IconButton>
      </Tooltip>
      {isListening && interimTranscript && (
        <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {interimTranscript}
        </Typography>
      )}
    </Box>
  );
}
