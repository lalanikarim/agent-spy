export type Theme = "light" | "dark";

// Theme token types for type safety
export interface ColorTokens {
  primary: string;
  "primary-hover": string;
  "primary-active": string;
  secondary: string;
  "secondary-hover": string;
  "secondary-active": string;
  background: string;
  surface: string;
  "surface-hover": string;
  "surface-active": string;
  text: string;
  "text-secondary": string;
  "text-muted": string;
  "text-inverse": string;
  border: string;
  "border-hover": string;
  "border-focus": string;
  success: string;
  "success-hover": string;
  warning: string;
  "warning-hover": string;
  error: string;
  "error-hover": string;
  info: string;
  "info-hover": string;
  // Status colors
  "status-running": string;
  "status-running-text": string;
  "status-completed": string;
  "status-completed-text": string;
  "status-failed": string;
  "status-failed-text": string;
  // Icon colors for ThemeToggle
  "icon-light": string;
  "icon-dark": string;
  // Dedicated hover colors for consistent hover states
  "hover-light": string;
  "hover-dark": string;
  "hover-text": string;
  "hover-border": string;
}

export interface SpacingTokens {
  "1": string;
  "2": string;
  "3": string;
  "4": string;
  "5": string;
  "6": string;
  "8": string;
  "10": string;
  "12": string;
}

export interface TypographyTokens {
  fontFamily: string;
  fontSize: {
    xs: string;
    sm: string;
    base: string;
    lg: string;
    xl: string;
    "2xl": string;
    "3xl": string;
  };
  fontWeight: {
    normal: string;
    medium: string;
    semibold: string;
    bold: string;
  };
  lineHeight: {
    tight: string;
    normal: string;
    relaxed: string;
  };
}

export interface ShadowTokens {
  sm: string;
  md: string;
  lg: string;
  xl: string;
}

export interface BorderRadiusTokens {
  sm: string;
  md: string;
  lg: string;
  xl: string;
  full: string;
}

export interface TransitionTokens {
  fast: string;
  normal: string;
  slow: string;
}

export interface ZIndexTokens {
  dropdown: string;
  sticky: string;
  fixed: string;
  "modal-backdrop": string;
  modal: string;
  popover: string;
  tooltip: string;
  toast: string;
}

export interface ThemeTokens {
  colors: ColorTokens;
  spacing: SpacingTokens;
  typography: TypographyTokens;
  shadows: ShadowTokens;
  borderRadius: BorderRadiusTokens;
  transitions: TransitionTokens;
  zIndex: ZIndexTokens;
}

// Light theme tokens
export const lightTokens: ThemeTokens = {
  colors: {
    primary: "#3b82f6",
    "primary-hover": "#2563eb",
    "primary-active": "#1d4ed8",
    secondary: "#6366f1",
    "secondary-hover": "#5855eb",
    "secondary-active": "#4f46e5",
    background: "#f8fafc",
    surface: "#ffffff",
    "surface-hover": "#f8fafc", // More subtle hover - same as background
    "surface-active": "#e2e8f0",
    text: "#1e293b",
    "text-secondary": "#64748b",
    "text-muted": "#94a3b8",
    "text-inverse": "#ffffff",
    border: "#e2e8f0",
    "border-hover": "#cbd5e1",
    "border-focus": "#3b82f6",
    success: "#10b981",
    "success-hover": "#059669",
    warning: "#f59e0b",
    "warning-hover": "#d97706",
    error: "#ef4444",
    "error-hover": "#dc2626",
    info: "#3b82f6",
    "info-hover": "#2563eb",
    // Status colors
    "status-running": "#e6f7ff",
    "status-running-text": "#1890ff",
    "status-completed": "#f6ffed",
    "status-completed-text": "#52c41a",
    "status-failed": "#fff2f0",
    "status-failed-text": "#ff4d4f",
    // Icon colors for ThemeToggle
    "icon-light": "#fbbf24", // yellow-400
    "icon-dark": "#d1d5db", // gray-300
    // Dedicated hover colors for consistent hover states
    "hover-light": "#e2e8f0", // slate-200 - more visible light hover
    "hover-dark": "#475569", // slate-600 - visible dark hover
    "hover-text": "#1e293b", // slate-800 - dark text on hover
    "hover-border": "#cbd5e1", // slate-300 - light border on hover
  },
  spacing: {
    "1": "4px",
    "2": "8px",
    "3": "12px",
    "4": "16px",
    "5": "20px",
    "6": "24px",
    "8": "32px",
    "10": "40px",
    "12": "48px",
  },
  typography: {
    fontFamily:
      "'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    fontSize: {
      xs: "12px",
      sm: "14px",
      base: "16px",
      lg: "18px",
      xl: "20px",
      "2xl": "24px",
      "3xl": "30px",
    },
    fontWeight: {
      normal: "400",
      medium: "500",
      semibold: "600",
      bold: "700",
    },
    lineHeight: {
      tight: "1.25",
      normal: "1.5",
      relaxed: "1.6",
    },
  },
  shadows: {
    sm: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
    md: "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
    lg: "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
    xl: "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)",
  },
  borderRadius: {
    sm: "4px",
    md: "8px",
    lg: "12px",
    xl: "16px",
    full: "9999px",
  },
  transitions: {
    fast: "150ms ease-in-out",
    normal: "250ms ease-in-out",
    slow: "350ms ease-in-out",
  },
  zIndex: {
    dropdown: "1000",
    sticky: "1020",
    fixed: "1030",
    "modal-backdrop": "1040",
    modal: "1050",
    popover: "1060",
    tooltip: "1070",
    toast: "1080",
  },
};

// Dark theme tokens
export const darkTokens: ThemeTokens = {
  colors: {
    primary: "#1a365d",
    "primary-hover": "#1e40af",
    "primary-active": "#1e3a8a",
    secondary: "#00d4ff",
    "secondary-hover": "#00b8e6",
    "secondary-active": "#0099cc",
    background: "#0f172a",
    surface: "#1e293b",
    "surface-hover": "#334155", // Lighter than surface for contrast
    "surface-active": "#475569",
    text: "#e2e8f0",
    "text-secondary": "#94a3b8",
    "text-muted": "#64748b",
    "text-inverse": "#0f172a",
    border: "#334155",
    "border-hover": "#475569",
    "border-focus": "#00d4ff",
    success: "#10b981",
    "success-hover": "#059669",
    warning: "#f59e0b",
    "warning-hover": "#d97706",
    error: "#ef4444",
    "error-hover": "#dc2626",
    info: "#00d4ff",
    "info-hover": "#00b8e6",
    // Status colors - Dark Mode
    "status-running": "rgba(0, 212, 255, 0.1)",
    "status-running-text": "#00d4ff",
    "status-completed": "rgba(16, 185, 129, 0.1)",
    "status-completed-text": "#10b981",
    "status-failed": "rgba(239, 68, 68, 0.1)",
    "status-failed-text": "#ef4444",
    // Icon colors for ThemeToggle
    "icon-light": "#fbbf24", // yellow-400
    "icon-dark": "#6b7280", // gray-500
    // Dedicated hover colors for consistent hover states
    "hover-light": "#64748b", // slate-500 - more visible light hover on dark
    "hover-dark": "#334155", // slate-700 - subtle dark hover
    "hover-text": "#e2e8f0", // slate-200 - light text on hover
    "hover-border": "#64748b", // slate-500 - dark border on hover
  },
  spacing: {
    "1": "4px",
    "2": "8px",
    "3": "12px",
    "4": "16px",
    "5": "20px",
    "6": "24px",
    "8": "32px",
    "10": "40px",
    "12": "48px",
  },
  typography: {
    fontFamily:
      "'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    fontSize: {
      xs: "12px",
      sm: "14px",
      base: "16px",
      lg: "18px",
      xl: "20px",
      "2xl": "24px",
      "3xl": "30px",
    },
    fontWeight: {
      normal: "400",
      medium: "500",
      semibold: "600",
      bold: "700",
    },
    lineHeight: {
      tight: "1.25",
      normal: "1.5",
      relaxed: "1.6",
    },
  },
  shadows: {
    sm: "0 1px 2px 0 rgb(0 0 0 / 0.3)",
    md: "0 4px 6px -1px rgb(0 0 0 / 0.4), 0 2px 4px -2px rgb(0 0 0 / 0.4)",
    lg: "0 10px 15px -3px rgb(0 0 0 / 0.4), 0 4px 6px -4px rgb(0 0 0 / 0.4)",
    xl: "0 20px 25px -5px rgb(0 0 0 / 0.4), 0 8px 10px -6px rgb(0 0 0 / 0.4)",
  },
  borderRadius: {
    sm: "4px",
    md: "8px",
    lg: "12px",
    xl: "16px",
    full: "9999px",
  },
  transitions: {
    fast: "150ms ease-in-out",
    normal: "250ms ease-in-out",
    slow: "350ms ease-in-out",
  },
  zIndex: {
    dropdown: "1000",
    sticky: "1020",
    fixed: "1030",
    "modal-backdrop": "1040",
    modal: "1050",
    popover: "1060",
    tooltip: "1070",
    toast: "1080",
  },
};

// Theme tokens mapping
export const themeTokens: Record<Theme, ThemeTokens> = {
  light: lightTokens,
  dark: darkTokens,
};

// Helper function to get theme tokens
export const getThemeTokens = (theme: Theme): ThemeTokens => {
  return themeTokens[theme];
};

// Helper function to get a specific token value
export const getThemeValue = (path: string, theme: Theme): string => {
  const tokens = getThemeTokens(theme);
  const keys = path.split(".");
  let value: any = tokens;

  for (const key of keys) {
    if (value && typeof value === "object" && key in value) {
      value = value[key];
    } else {
      console.warn(`Theme token not found: ${path}`);
      return "";
    }
  }

  return value;
};
