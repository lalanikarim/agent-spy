import React, { createContext, useEffect, useState } from "react";
import type { Theme } from "../theme/tokens";
import { applyThemeToDocument } from "../theme/utils";

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
    const savedTheme = localStorage.getItem("agent-spy-theme") as Theme;
    if (savedTheme && (savedTheme === "light" || savedTheme === "dark")) {
      return savedTheme;
    }

    // Check system preference
    if (
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
    ) {
      return "dark";
    }

    return "light";
  });

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
    localStorage.setItem("agent-spy-theme", newTheme);

    // Apply theme using new utility function
    applyThemeToDocument(newTheme);
  };

  const toggleTheme = () => {
    const newTheme = theme === "light" ? "dark" : "light";
    setTheme(newTheme);
  };

  // Apply theme to document on mount and theme change
  useEffect(() => {
    // Apply theme using new utility function
    applyThemeToDocument(theme);

    // Add theme transition class to body for smooth transitions
    document.body.classList.add("theme-transition");

    // Remove transition class after transition completes to avoid affecting initial load
    const timer = setTimeout(() => {
      document.body.classList.remove("theme-transition");
    }, 250);

    return () => clearTimeout(timer);
  }, [theme]);

  // Listen for system theme changes
  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

    const handleChange = (e: MediaQueryListEvent) => {
      // Only auto-switch if user hasn't manually set a preference
      const savedTheme = localStorage.getItem("agent-spy-theme");
      if (!savedTheme) {
        setTheme(e.matches ? "dark" : "light");
      }
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, []);

  const value: ThemeContextType = {
    theme,
    toggleTheme,
    setTheme,
  };

  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
};

// Export the context for use in hooks
export { ThemeContext };
