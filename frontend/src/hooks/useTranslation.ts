import { useState, useCallback, useEffect } from 'react';
import { translationApi } from '../services/api/translation';
import type { Language } from '../types';

export function useTranslation(defaultLanguage = 'en') {
  const [targetLanguage, setTargetLanguage] = useState(defaultLanguage);
  const [translatedText, setTranslatedText] = useState('');
  const [languages, setLanguages] = useState<Language[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const translate = useCallback(async (text: string, target?: string) => {
    if (!text.trim()) { setTranslatedText(''); return; }
    try {
      setLoading(true);
      setError(null);
      const result = await translationApi.translate(text, target || targetLanguage);
      setTranslatedText(result.translatedText);
      return result.translatedText;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Translation failed');
      return null;
    } finally {
      setLoading(false);
    }
  }, [targetLanguage]);

  const detectLanguage = useCallback(async (text: string) => {
    try {
      const result = await translationApi.detect(text);
      return result;
    } catch {
      return null;
    }
  }, []);

  const fetchLanguages = useCallback(async () => {
    try {
      const result = await translationApi.getLanguages();
      setLanguages(result);
    } catch {
      setLanguages([
        { code: 'en', name: 'English', nativeName: 'English' },
        { code: 'es', name: 'Spanish', nativeName: 'Español' },
        { code: 'fr', name: 'French', nativeName: 'Français' },
        { code: 'de', name: 'German', nativeName: 'Deutsch' },
        { code: 'ar', name: 'Arabic', nativeName: 'العربية' },
        { code: 'pt', name: 'Portuguese', nativeName: 'Português' },
        { code: 'zh', name: 'Chinese', nativeName: '中文' },
        { code: 'ja', name: 'Japanese', nativeName: '日本語' },
      ]);
    }
  }, []);

  useEffect(() => {
    fetchLanguages();
  }, [fetchLanguages]);

  return {
    targetLanguage,
    setTargetLanguage,
    translatedText,
    languages,
    loading,
    error,
    translate,
    detectLanguage,
  };
}
