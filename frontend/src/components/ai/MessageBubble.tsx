import { Box, Typography, Avatar } from '@mui/material';
import { SmartToy, Person } from '@mui/icons-material';
import type { Message } from '../../types';

interface MessageBubbleProps {
  message: Message;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'flex-start', flexDirection: isUser ? 'row-reverse' : 'row' }}>
      <Avatar
        sx={{
          width: 36,
          height: 36,
          bgcolor: isUser ? 'primary.main' : 'secondary.main',
          color: isUser ? 'white' : 'black',
        }}
      >
        {isUser ? <Person sx={{ fontSize: 20 }} /> : <SmartToy sx={{ fontSize: 20 }} />}
      </Avatar>

      <Box sx={{ maxWidth: '75%' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5, flexDirection: isUser ? 'row-reverse' : 'row' }}>
          <Typography variant="caption" fontWeight={600} color="text.secondary">
            {isUser ? 'You' : 'StadiumOS AI'}
          </Typography>
          {message.agent && !isUser && (
            <Typography variant="caption" color="secondary.main" sx={{ fontSize: '0.65rem' }}>
              ({message.agent})
            </Typography>
          )}
          <Typography variant="caption" color="text.secondary">
            {new Date(message.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </Typography>
        </Box>

        <Box
          sx={{
            px: 2,
            py: 1.5,
            borderRadius: 2,
            backgroundColor: isUser ? 'primary.main' : 'background.paper',
            color: isUser ? 'white' : 'text.primary',
            border: isUser ? 'none' : '1px solid',
            borderColor: 'divider',
            '& p': { m: 0 },
            '& p + p': { mt: 1 },
            whiteSpace: 'pre-wrap',
          }}
        >
          <Typography variant="body2" sx={{ lineHeight: 1.6 }}>{message.content}</Typography>
        </Box>

        {message.sources && message.sources.length > 0 && (
          <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {message.sources.map((source, idx) => (
              <Typography key={idx} variant="caption" sx={{ px: 1, py: 0.25, borderRadius: 1, backgroundColor: 'action.hover', color: 'text.secondary', fontSize: '0.65rem' }}>
                {source}
              </Typography>
            ))}
          </Box>
        )}
      </Box>
    </Box>
  );
}
