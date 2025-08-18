import type { Theme, ThemeTokens } from "./tokens";
import { getThemeTokens, getThemeValue } from "./tokens";

// Generate CSS custom properties from theme tokens
export const createCSSVariables = (theme: Theme): Record<string, string> => {
  const tokens = getThemeTokens(theme);

  const cssVars: Record<string, string> = {};

  // Colors
  Object.entries(tokens.colors).forEach(([key, value]) => {
    cssVars[`--color-${key}`] = value;
  });

  // Spacing
  Object.entries(tokens.spacing).forEach(([key, value]) => {
    cssVars[`--space-${key}`] = value;
  });

  // Typography
  cssVars["--font-family"] = tokens.typography.fontFamily;
  Object.entries(tokens.typography.fontSize).forEach(([key, value]) => {
    cssVars[`--font-size-${key}`] = value;
  });
  Object.entries(tokens.typography.fontWeight).forEach(([key, value]) => {
    cssVars[`--font-weight-${key}`] = value;
  });
  Object.entries(tokens.typography.lineHeight).forEach(([key, value]) => {
    cssVars[`--line-height-${key}`] = value;
  });

  // Shadows
  Object.entries(tokens.shadows).forEach(([key, value]) => {
    cssVars[`--shadow-${key}`] = value;
  });

  // Border radius
  Object.entries(tokens.borderRadius).forEach(([key, value]) => {
    cssVars[`--radius-${key}`] = value;
  });

  // Transitions
  Object.entries(tokens.transitions).forEach(([key, value]) => {
    cssVars[`--transition-${key}`] = value;
  });

  // Z-index
  Object.entries(tokens.zIndex).forEach(([key, value]) => {
    cssVars[`--z-${key}`] = value;
  });

  return cssVars;
};

// Apply CSS variables to document root
export const applyThemeToDocument = (theme: Theme): void => {
  const cssVars = createCSSVariables(theme);

  Object.entries(cssVars).forEach(([property, value]) => {
    document.documentElement.style.setProperty(property, value);
  });

  // Set data-theme attribute
  document.documentElement.setAttribute("data-theme", theme);

  // Apply Tailwind dark mode class
  if (theme === "dark") {
    document.documentElement.classList.add("dark");
  } else {
    document.documentElement.classList.remove("dark");
  }
};

// Create theme-aware style objects
export const createThemeStyles = (theme: Theme) => {
  const tokens = getThemeTokens(theme);

  return {
    // Common style combinations
    card: {
      base: {
        backgroundColor: tokens.colors.surface,
        borderColor: tokens.colors.border,
        borderRadius: tokens.borderRadius.lg,
        boxShadow: tokens.shadows.md,
        transition: tokens.transitions.normal,
      },
      hover: {
        backgroundColor: tokens.colors["surface-hover"],
        borderColor: tokens.colors["border-hover"],
        boxShadow: tokens.shadows.lg,
      },
      active: {
        backgroundColor: tokens.colors["surface-active"],
        borderColor: tokens.colors["border-hover"],
      },
    },
    button: {
      primary: {
        backgroundColor: tokens.colors.primary,
        color: tokens.colors["text-inverse"],
        borderColor: tokens.colors.primary,
        borderRadius: tokens.borderRadius.md,
        transition: tokens.transitions.normal,
      },
      secondary: {
        backgroundColor: tokens.colors.secondary,
        color: tokens.colors["text-inverse"],
        borderColor: tokens.colors.secondary,
        borderRadius: tokens.borderRadius.md,
        transition: tokens.transitions.normal,
      },
      ghost: {
        backgroundColor: "transparent",
        color: tokens.colors.text,
        borderColor: "transparent",
        borderRadius: tokens.borderRadius.md,
        transition: tokens.transitions.normal,
      },
    },
    text: {
      primary: {
        color: tokens.colors.text,
        fontFamily: tokens.typography.fontFamily,
      },
      secondary: {
        color: tokens.colors["text-secondary"],
        fontFamily: tokens.typography.fontFamily,
      },
      muted: {
        color: tokens.colors["text-muted"],
        fontFamily: tokens.typography.fontFamily,
      },
      inverse: {
        color: tokens.colors["text-inverse"],
        fontFamily: tokens.typography.fontFamily,
      },
    },
    input: {
      base: {
        backgroundColor: tokens.colors.surface,
        borderColor: tokens.colors.border,
        color: tokens.colors.text,
        borderRadius: tokens.borderRadius.md,
        transition: tokens.transitions.normal,
      },
      focus: {
        borderColor: tokens.colors["border-focus"],
        boxShadow: `0 0 0 2px ${tokens.colors["border-focus"]}20`,
      },
      hover: {
        borderColor: tokens.colors["border-hover"],
      },
    },
  };
};

// Get theme-aware color values
export const getThemeColor = (
  colorKey: keyof ThemeTokens["colors"],
  theme: Theme
): string => {
  return getThemeValue(`colors.${colorKey}`, theme);
};

// Get theme-aware spacing values
export const getThemeSpacing = (
  spacingKey: keyof ThemeTokens["spacing"],
  theme: Theme
): string => {
  return getThemeValue(`spacing.${spacingKey}`, theme);
};

// Get theme-aware typography values
export const getThemeTypography = (
  typographyKey: string,
  theme: Theme
): string => {
  return getThemeValue(`typography.${typographyKey}`, theme);
};

// Create responsive theme styles
export const createResponsiveThemeStyles = (theme: Theme) => {
  const baseStyles = createThemeStyles(theme);

  return {
    ...baseStyles,
    // Add responsive variants
    card: {
      ...baseStyles.card,
      mobile: {
        ...baseStyles.card.base,
        padding: getThemeSpacing("4", theme),
      },
      tablet: {
        ...baseStyles.card.base,
        padding: getThemeSpacing("6", theme),
      },
      desktop: {
        ...baseStyles.card.base,
        padding: getThemeSpacing("8", theme),
      },
    },
  };
};

// Validate theme tokens
export const validateThemeTokens = (theme: Theme): boolean => {
  const tokens = getThemeTokens(theme);

  // Check if all required color tokens exist
  const requiredColors = ["primary", "background", "surface", "text", "border"];

  for (const color of requiredColors) {
    if (!tokens.colors[color as keyof typeof tokens.colors]) {
      console.error(`Missing required color token: ${color}`);
      return false;
    }
  }

  return true;
};

// Create theme transition styles
export const createThemeTransitionStyles = (theme: Theme) => {
  const tokens = getThemeTokens(theme);

  return {
    transition: tokens.transitions.normal,
    transitionFast: tokens.transitions.fast,
    transitionSlow: tokens.transitions.slow,
  };
};

// Re-export getThemeValue from tokens for convenience
export { getThemeValue } from "./tokens";
