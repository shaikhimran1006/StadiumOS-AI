import { useState, useCallback, useRef } from 'react';
import type { Message, ChatRequest } from '../types';
import { chatApi } from '../services/api/chat';

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isTyping, setIsTyping] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(async (content: string, language?: string, agent?: string) => {
    if (!content.trim()) return;

    const userMessage: Message = {
      id: `temp-${Date.now()}`,
      conversationId: conversationId || '',
      role: 'user',
      content: content.trim(),
      createdAt: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setIsTyping(true);
    setError(null);

    try {
      abortControllerRef.current = new AbortController();
      const request: ChatRequest = { message: content.trim(), language, agent };
      if (conversationId) request.conversationId = conversationId;

      const response = await chatApi.sendMessage(request);

      setMessages((prev) => {
        const withoutTemp = prev.filter((m) => !m.id.startsWith('temp-'));
        return [...withoutTemp, userMessage, response.message];
      });
      setConversationId(response.conversationId);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to send message');
      setMessages((prev) => prev.filter((m) => !m.id.startsWith('temp-')));
    } finally {
      setLoading(false);
      setIsTyping(false);
      abortControllerRef.current = null;
    }
  }, [conversationId]);

  const loadConversation = useCallback(async (id: string) => {
    try {
      setLoading(true);
      const history = await chatApi.getConversationHistory(id);
      setMessages(history);
      setConversationId(id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load conversation');
    } finally {
      setLoading(false);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setConversationId(null);
    setError(null);
  }, []);

  const loadConversations = useCallback(async () => {
    return chatApi.getConversations();
  }, []);

  return {
    messages,
    conversationId,
    loading,
    error,
    isTyping,
    sendMessage,
    loadConversation,
    loadConversations,
    clearMessages,
  };
}
