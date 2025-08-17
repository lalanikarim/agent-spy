import React, { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface ThemeProviderProps {
  children: React.ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [theme, setThemeState] = useState<Theme>(() => {
    // Check localStorage first, then system preference, default to light
    const savedTheme = localStorage.getItem('agent-spy-theme') as Theme;
    if (savedTheme && (savedTheme === 'light' || savedTheme === 'dark')) {
      return savedTheme;
    }
    
    // Check system preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    
    return 'light';
  });

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
    localStorage.setItem('agent-spy-theme', newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
  };

  // Apply theme to document on mount and theme change
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    
    // Add theme transition class to body for smooth transitions
    document.body.classList.add('theme-transition');
    
    // Remove transition class after transition completes to avoid affecting initial load
    const timer = setTimeout(() => {
      document.body.classList.remove('theme-transition');
    }, 250);
    
    return () => clearTimeout(timer);
  }, [theme]);

  // Listen for system theme changes
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = (e: MediaQueryListEvent) => {
      // Only auto-switch if user hasn't manually set a preference
      const savedTheme = localStorage.getItem('agent-spy-theme');
      if (!savedTheme) {
        setTheme(e.matches ? 'dark' : 'light');
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  const value: ThemeContextType = {
    theme,
    toggleTheme,
    setTheme,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

// Hook for getting theme-aware styles
export const useThemeStyles = () => {
  const { theme } = useTheme();
  
  return {
    isDark: theme === 'dark',
    isLight: theme === 'light',
    theme,
    // Common style combinations
    cardStyle: 'bg-surface border border-border rounded-theme-lg shadow-theme-md',
    buttonStyle: 'bg-primary hover:bg-primary-hover text-text-inverse px-4 py-2 rounded-theme-md transition-colors duration-theme-normal',
    inputStyle: 'bg-surface border border-border focus:border-border-focus rounded-theme-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-border-focus focus:ring-opacity-50',
    textStyle: 'text-text',
    textSecondaryStyle: 'text-text-secondary',
    textMutedStyle: 'text-text-muted',
  };
};
