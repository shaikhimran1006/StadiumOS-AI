import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';

interface ThemeContextType {
  mode: 'dark' | 'light';
  toggleMode: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeContextProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<'dark' | 'light'>(() => {
    return (localStorage.getItem('stadiumos_theme') as 'dark' | 'light') || 'dark';
  });

  const toggleMode = useCallback(() => {
    setMode((prev) => {
      const next = prev === 'dark' ? 'light' : 'dark';
      localStorage.setItem('stadiumos_theme', next);
      return next;
    });
  }, []);

  return (
    <ThemeContext.Provider value={{ mode, toggleMode }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useThemeContext(): ThemeContextType {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useThemeContext must be used within ThemeContextProvider');
  return context;
}
