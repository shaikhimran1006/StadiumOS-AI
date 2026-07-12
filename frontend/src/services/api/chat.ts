import apiClient from './client';
import type { ChatRequest, ChatResponse, Conversation, Message, PaginatedResponse } from '../../types';

export const chatApi = {
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const { data } = await apiClient.post<ChatResponse>('/chat/send', request);
    return data;
  },

  async getConversations(page = 1, pageSize = 20): Promise<PaginatedResponse<Conversation>> {
    const { data } = await apiClient.get('/chat/conversations', { params: { page, pageSize } });
    return data;
  },

  async getConversationHistory(conversationId: string): Promise<Message[]> {
    const { data } = await apiClient.get<Message[]>(`/chat/conversations/${conversationId}/messages`);
    return data;
  },

  async closeConversation(conversationId: string): Promise<void> {
    await apiClient.post(`/chat/conversations/${conversationId}/close`);
  },

  async deleteConversation(conversationId: string): Promise<void> {
    await apiClient.delete(`/chat/conversations/${conversationId}`);
  },
};
