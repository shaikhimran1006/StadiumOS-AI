import { useState, useRef, useEffect, useCallback } from 'react';
import { Box, TextField, IconButton, Typography, Paper, Chip, Divider } from '@mui/material';
import { Send, Mic, MicOff, SmartToy } from '@mui/icons-material';
import MessageBubble from './MessageBubble';
import AgentIndicator from './AgentIndicator';
import VoiceInput from './VoiceInput';
import { useChat } from '../../hooks/useChat';
import { useSpeech } from '../../hooks/useSpeech';
import { useTranslation } from '../../hooks/useTranslation';
import type { Message } from '../../types';

export default function ChatInterface() {
  const { messages, loading, error, isTyping, sendMessage } = useChat();
  const { isListening, transcript, interimTranscript, isSpeaking, isSupported: speechSupported, startListening, stopListening } = useSpeech();
  const { targetLanguage, setTargetLanguage, languages, translate } = useTranslation();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, scrollToBottom]);

  useEffect(() => {
    if (transcript) setInput(transcript);
  }, [transcript]);

  const handleSend = useCallback(() => {
    if (!input.trim() || loading) return;
    sendMessage(input.trim(), targetLanguage);
    setInput('');
  }, [input, loading, sendMessage, targetLanguage]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }, [handleSend]);

  const handleVoiceToggle = useCallback(() => {
    if (isListening) stopListening();
    else startListening();
  }, [isListening, startListening, stopListening]);

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: 'calc(100vh - 128px)' }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <SmartToy sx={{ color: 'secondary.main' }} />
          <Typography variant="h6" fontWeight={600}>AI Stadium Assistant</Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          {languages.length > 0 && (
            <select
              value={targetLanguage}
              onChange={(e) => setTargetLanguage(e.target.value)}
              className="bg-dark-card border border-dark-border rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-stadium-blue"
            >
              {languages.map((lang) => (
                <option key={lang.code} value={lang.code}>{lang.name}</option>
              ))}
            </select>
          )}
        </Box>
      </Box>

      <Paper sx={{ flex: 1, overflow: 'auto', p: 2, backgroundColor: 'background.paper', display: 'flex', flexDirection: 'column' }}>
        {messages.length === 0 && (
          <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 2, opacity: 0.7 }}>
            <SmartToy sx={{ fontSize: 64, color: 'secondary.main' }} />
            <Typography variant="h5" fontWeight={600}>How can I help you today?</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', maxWidth: 500 }}>
              I can help with stadium operations, security alerts, event management, navigation, and more. Ask me anything!
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 2, justifyContent: 'center' }}>
              {['Show active alerts', 'Navigate to Sector A', 'Report an incident', 'Event schedule'].map((suggestion) => (
                <Chip
                  key={suggestion}
                  label={suggestion}
                  onClick={() => { setInput(suggestion); }}
                  variant="outlined"
                  sx={{ cursor: 'pointer', '&:hover': { backgroundColor: 'action.hover' } }}
                />
              ))}
            </Box>
          </Box>
        )}

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          {messages.map((msg: Message) => (
            <MessageBubble key={msg.id} message={msg} />
          ))}
          {isTyping && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 2 }}>
              <SmartToy sx={{ color: 'secondary.main', fontSize: 20 }} />
              <AgentIndicator />
              <Box sx={{ display: 'flex', gap: 0.5, ml: 1 }}>
                <Box className="typing-dot" sx={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: 'text.secondary' }} />
                <Box className="typing-dot" sx={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: 'text.secondary' }} />
                <Box className="typing-dot" sx={{ width: 6, height: 6, borderRadius: '50%', backgroundColor: 'text.secondary' }} />
              </Box>
            </Box>
          )}
        </Box>
        <div ref={messagesEndRef} />
      </Paper>

      {error && (
        <Box sx={{ px: 2, py: 1 }}>
          <Typography variant="caption" color="error">{error}</Typography>
        </Box>
      )}

      <Divider />

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, pt: 2 }}>
        {speechSupported && (
          <VoiceInput
            isListening={isListening}
            onToggle={handleVoiceToggle}
            interimTranscript={interimTranscript}
          />
        )}
        <TextField
          inputRef={inputRef}
          fullWidth
          multiline
          maxRows={4}
          placeholder="Type your message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={loading}
          sx={{
            '& .MuiOutlinedInput-root': {
              backgroundColor: 'background.paper',
              borderRadius: 3,
            },
          }}
        />
        <IconButton
          onClick={handleSend}
          disabled={!input.trim() || loading}
          sx={{
            width: 48,
            height: 48,
            backgroundColor: 'secondary.main',
            color: 'black',
            '&:hover': { backgroundColor: 'secondary.dark' },
            '&:disabled': { backgroundColor: 'action.disabledBackground' },
          }}
        >
          <Send />
        </IconButton>
      </Box>
    </Box>
  );
}
