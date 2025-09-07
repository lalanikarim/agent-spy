import { useContext } from "react";
import { ThemeContext } from "../contexts/ThemeContext";
import {
  createThemeStyles,
  getThemeColor,
  getThemeSpacing,
  getThemeTypography,
  getThemeValue,
} from "../theme/utils";

// Hook for getting theme context
export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
};

// Hook for getting theme-aware styles
export const useThemeStyles = () => {
  const { theme } = useTheme();

  return {
    isDark: theme === "dark",
    isLight: theme === "light",
    theme,
    // Common style combinations
    cardStyle:
      "bg-surface border border-border rounded-theme-lg shadow-theme-md",
    buttonStyle:
      "bg-primary hover:bg-primary-hover text-text-inverse px-4 py-2 rounded-theme-md transition-colors duration-theme-normal",
    inputStyle:
      "bg-surface border border-border focus:border-border-focus rounded-theme-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-border-focus focus:ring-opacity-50",
    textStyle: "text-text",
    textSecondaryStyle: "text-text-secondary",
    textMutedStyle: "text-text-muted",
  };
};

// Hook for getting theme colors
export const useThemeColors = () => {
  const { theme } = useTheme();

  return {
    getColor: (colorKey: string) => getThemeColor(colorKey as any, theme),
    isDark: theme === "dark",
    isLight: theme === "light",
    theme,
  };
};

// Hook for getting theme spacing
export const useThemeSpacing = () => {
  const { theme } = useTheme();

  return {
    getSpacing: (spacingKey: string) =>
      getThemeSpacing(spacingKey as any, theme),
    theme,
  };
};

// Hook for getting theme-aware style objects
export const useThemeStyleObjects = () => {
  const { theme } = useTheme();

  return createThemeStyles(theme);
};

// Hook for getting theme typography
export const useThemeTypography = () => {
  const { theme } = useTheme();

  return {
    getFontSize: (size: string) => getThemeTypography(`fontSize.${size}`, theme),
    getFontWeight: (weight: string) => getThemeTypography(`fontWeight.${weight}`, theme),
    getLineHeight: (height: string) => getThemeTypography(`lineHeight.${height}`, theme),
    fontFamily: getThemeTypography('fontFamily', theme),
    theme,
  };
};

// Hook for getting theme shadows
export const useThemeShadows = () => {
  const { theme } = useTheme();

  return {
    getShadow: (shadow: 'sm' | 'md' | 'lg' | 'xl') => getThemeValue(`shadows.${shadow}`, theme),
    theme,
  };
};

// Hook for getting theme border radius
export const useThemeBorderRadius = () => {
  const { theme } = useTheme();

  return {
    getRadius: (radius: 'sm' | 'md' | 'lg' | 'xl' | 'full') => getThemeValue(`borderRadius.${radius}`, theme),
    theme,
  };
};

// Hook for getting theme transitions
export const useThemeTransitions = () => {
  const { theme } = useTheme();

  return {
    getTransition: (transition: 'fast' | 'normal' | 'slow') => getThemeValue(`transitions.${transition}`, theme),
    theme,
  };
};

// Hook for getting theme z-index values
export const useThemeZIndex = () => {
  const { theme } = useTheme();

  return {
    getZIndex: (zIndex: 'dropdown' | 'sticky' | 'fixed' | 'modal-backdrop' | 'modal' | 'popover' | 'tooltip' | 'toast') =>
      getThemeValue(`zIndex.${zIndex}`, theme),
    theme,
  };
};

// Hook for getting theme status colors
export const useThemeStatusColors = () => {
  const { theme } = useTheme();

  return {
    getStatusColor: (status: 'running' | 'completed' | 'failed') => getThemeColor(`status-${status}`, theme),
    getStatusTextColor: (status: 'running' | 'completed' | 'failed') => getThemeColor(`status-${status}-text`, theme),
    theme,
  };
};

// Hook for getting theme semantic colors
export const useThemeSemanticColors = () => {
  const { theme } = useTheme();

  return {
    getSemanticColor: (semantic: 'success' | 'warning' | 'error' | 'info') => getThemeColor(semantic, theme),
    getSemanticHoverColor: (semantic: 'success' | 'warning' | 'error' | 'info') => getThemeColor(`${semantic}-hover`, theme),
    theme,
  };
};

// Hook for getting theme surface colors
export const useThemeSurfaceColors = () => {
  const { theme } = useTheme();

  return {
    getSurfaceColor: (surface: 'background' | 'surface' | 'surface-hover' | 'surface-active') => getThemeColor(surface, theme),
    theme,
  };
};

// Hook for getting theme text colors
export const useThemeTextColors = () => {
  const { theme } = useTheme();

  return {
    getTextColor: (text: 'text' | 'text-secondary' | 'text-muted' | 'text-inverse') => getThemeColor(text, theme),
    theme,
  };
};

// Hook for getting theme border colors
export const useThemeBorderColors = () => {
  const { theme } = useTheme();

  return {
    getBorderColor: (border: 'border' | 'border-hover' | 'border-focus') => getThemeColor(border, theme),
    theme,
  };
};
