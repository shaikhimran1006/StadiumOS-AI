import apiClient from '../api/client';

interface SpeechCallbacks {
  onResult: (transcript: string, isFinal: boolean) => void;
  onError: (error: string) => void;
  onEnd: () => void;
}

let recognition: SpeechRecognition | null = null;

export const speechService = {
  isSupported(): boolean {
    return 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
  },

  startRecognition(language: string, callbacks: SpeechCallbacks): void {
    if (!this.isSupported()) {
      callbacks.onError('Speech recognition is not supported in this browser');
      return;
    }

    const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognitionAPI();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = language;

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let finalTranscript = '';
      let interimTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }

      if (finalTranscript) callbacks.onResult(finalTranscript, true);
      else if (interimTranscript) callbacks.onResult(interimTranscript, false);
    };

    recognition.onerror = (event) => {
      callbacks.onError(event.error);
    };

    recognition.onend = () => {
      callbacks.onEnd();
    };

    recognition.start();
  },

  stopRecognition(): string {
    if (recognition) {
      recognition.stop();
      recognition = null;
    }
    return '';
  },

  async synthesize(text: string, language: string): Promise<void> {
    try {
      const { data } = await apiClient.post('/speech/synthesize', { text, language }, { responseType: 'blob' });
      const audioUrl = URL.createObjectURL(data);
      const audio = new Audio(audioUrl);
      audio.onended = () => URL.revokeObjectURL(audioUrl);
      await audio.play();
    } catch {
      if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = language;
        window.speechSynthesis.speak(utterance);
      }
    }
  },

  getRecognitionState(): boolean {
    return recognition !== null;
  },
};
