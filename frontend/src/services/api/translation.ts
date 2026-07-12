import apiClient from './client';
import type { TranslationResponse, Language } from '../../types';

export const translationApi = {
  async translate(text: string, targetLanguage: string, sourceLanguage = 'auto'): Promise<TranslationResponse> {
    const { data } = await apiClient.post('/translation/translate', { text, targetLanguage, sourceLanguage });
    return data;
  },

  async detect(text: string): Promise<{ language: string; confidence: number }> {
    const { data } = await apiClient.post('/translation/detect', { text });
    return data;
  },

  async getLanguages(): Promise<Language[]> {
    const { data } = await apiClient.get('/translation/languages');
    return data;
  },
};
