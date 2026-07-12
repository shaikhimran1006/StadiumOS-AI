import { useState, useCallback, useRef } from 'react';
import { speechService } from '../services/speech/speech';

export function useSpeech(language = 'en-US') {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isSpeaking, setIsSpeaking] = useState(false);

  const startListening = useCallback(() => {
    setError(null);
    setTranscript('');
    setInterimTranscript('');

    speechService.startRecognition(language, {
      onResult: (text, isFinal) => {
        if (isFinal) {
          setTranscript((prev) => prev + text);
          setInterimTranscript('');
        } else {
          setInterimTranscript(text);
        }
      },
      onError: (err) => {
        setError(err);
        setIsListening(false);
      },
      onEnd: () => {
        setIsListening(false);
      },
    });

    setIsListening(true);
  }, [language]);

  const stopListening = useCallback(() => {
    speechService.stopRecognition();
    setIsListening(false);
  }, []);

  const speak = useCallback(async (text: string) => {
    setIsSpeaking(true);
    try {
      await speechService.synthesize(text, language);
    } finally {
      setIsSpeaking(false);
    }
  }, [language]);

  const resetTranscript = useCallback(() => {
    setTranscript('');
    setInterimTranscript('');
  }, []);

  const isSupported = speechService.isSupported();

  return {
    isListening,
    transcript,
    interimTranscript,
    error,
    isSpeaking,
    isSupported,
    startListening,
    stopListening,
    speak,
    resetTranscript,
  };
}
