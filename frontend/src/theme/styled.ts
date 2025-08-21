import React from "react";
import type { Theme } from "./tokens";
import { getThemeTokens } from "./tokens";

/**
 * Theme-aware style object type
 */
export interface ThemeStyles {
  [key: string]: string | number | ThemeStyles;
}

/**
 * Styled component props interface
 */
export interface StyledComponentProps {
  theme?: Theme;
  className?: string;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}

/**
 * Create a theme-aware styled component
 */
export const createStyledComponent = (
  element: keyof React.JSX.IntrinsicElements,
  styles: ThemeStyles | ((theme: Theme) => ThemeStyles)
) => {
  const StyledComponent: React.FC<StyledComponentProps> = ({
    theme = "light",
    className = "",
    style = {},
    children,
    ...props
  }) => {
    const tokens = getThemeTokens(theme);
    const resolvedStyles =
      typeof styles === "function" ? styles(theme) : styles;

    // Convert theme styles to CSS properties
    const cssStyles = convertThemeStylesToCSS(resolvedStyles, tokens);

    return React.createElement(
      element,
      {
        className,
        style: { ...cssStyles, ...style },
        ...props,
      },
      children
    );
  };

  return StyledComponent;
};

/**
 * Convert theme styles object to CSS properties
 */
const convertThemeStylesToCSS = (
  styles: ThemeStyles,
  tokens: any
): React.CSSProperties => {
  const css: React.CSSProperties = {};

  Object.entries(styles).forEach(([key, value]) => {
    if (typeof value === "string" || typeof value === "number") {
      // Handle theme token references (e.g., "colors.primary")
      if (typeof value === "string" && value.includes(".")) {
        const tokenValue = getThemeValue(value, tokens);
        if (tokenValue) {
          (css as any)[convertToCamelCase(key)] = tokenValue;
        } else {
          (css as any)[convertToCamelCase(key)] = value;
        }
      } else {
        (css as any)[convertToCamelCase(key)] = value;
      }
    } else if (typeof value === "object" && value !== null) {
      // Handle nested objects (e.g., pseudo-selectors)
      const nestedCSS = convertThemeStylesToCSS(value, tokens);
      Object.assign(css, nestedCSS);
    }
  });

  return css;
};

/**
 * Get theme value from nested path
 */
const getThemeValue = (path: string, tokens: any): string | null => {
  const keys = path.split(".");
  let value: any = tokens;

  for (const key of keys) {
    if (value && typeof value === "object" && key in value) {
      value = value[key];
    } else {
      return null;
    }
  }

  return typeof value === "string" ? value : null;
};

/**
 * Convert kebab-case to camelCase
 */
const convertToCamelCase = (str: string): string => {
  return str.replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
};

/**
 * Predefined styled components
 */
export const styled = {
  div: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("div", styles),

  button: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("button", styles),

  span: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("span", styles),

  p: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("p", styles),

  h1: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("h1", styles),

  h2: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("h2", styles),

  h3: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("h3", styles),

  h4: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("h4", styles),

  h5: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("h5", styles),

  h6: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("h6", styles),

  section: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("section", styles),

  article: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("article", styles),

  header: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("header", styles),

  footer: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("footer", styles),

  nav: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("nav", styles),

  aside: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("aside", styles),

  main: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("main", styles),

  form: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("form", styles),

  input: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("input", styles),

  label: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("label", styles),

  ul: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("ul", styles),

  ol: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("ol", styles),

  li: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("li", styles),

  a: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("a", styles),

  img: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("img", styles),

  table: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("table", styles),

  tr: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("tr", styles),

  td: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("td", styles),

  th: (styles: ThemeStyles | ((theme: Theme) => ThemeStyles)) =>
    createStyledComponent("th", styles),
};

/**
 * Utility function to create theme-aware styles
 */
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
      elevated: {
        backgroundColor: tokens.colors.surface,
        borderColor: tokens.colors.border,
        borderRadius: tokens.borderRadius.lg,
        boxShadow: tokens.shadows.lg,
        transition: tokens.transitions.normal,
      },
    },

    button: {
      primary: {
        backgroundColor: tokens.colors.primary,
        color: tokens.colors["text-inverse"],
        borderColor: tokens.colors.primary,
        borderRadius: tokens.borderRadius.md,
        transition: tokens.transitions.normal,
        padding: `${tokens.spacing["3"]} ${tokens.spacing["4"]}`,
        fontSize: tokens.typography.fontSize.base,
        fontWeight: tokens.typography.fontWeight.medium,
        cursor: "pointer",
        border: "none",
        outline: "none",
        "&:hover": {
          backgroundColor: tokens.colors["primary-hover"],
          borderColor: tokens.colors["primary-hover"],
        },
        "&:active": {
          backgroundColor: tokens.colors["primary-active"],
          borderColor: tokens.colors["primary-active"],
        },
      },

      secondary: {
        backgroundColor: tokens.colors.secondary,
        color: tokens.colors["text-inverse"],
        borderColor: tokens.colors.secondary,
        borderRadius: tokens.borderRadius.md,
        transition: tokens.transitions.normal,
        padding: `${tokens.spacing["3"]} ${tokens.spacing["4"]}`,
        fontSize: tokens.typography.fontSize.base,
        fontWeight: tokens.typography.fontWeight.medium,
        cursor: "pointer",
        border: "none",
        outline: "none",
        "&:hover": {
          backgroundColor: tokens.colors["secondary-hover"],
          borderColor: tokens.colors["secondary-hover"],
        },
        "&:active": {
          backgroundColor: tokens.colors["secondary-active"],
          borderColor: tokens.colors["secondary-active"],
        },
      },

      ghost: {
        backgroundColor: "transparent",
        color: tokens.colors.text,
        borderColor: "transparent",
        borderRadius: tokens.borderRadius.md,
        transition: tokens.transitions.normal,
        padding: `${tokens.spacing["3"]} ${tokens.spacing["4"]}`,
        fontSize: tokens.typography.fontSize.base,
        fontWeight: tokens.typography.fontWeight.medium,
        cursor: "pointer",
        border: "none",
        outline: "none",
        "&:hover": {
          backgroundColor: tokens.colors["surface-hover"],
          color: tokens.colors.text,
        },
      },
    },

    text: {
      primary: {
        color: tokens.colors.text,
        fontFamily: tokens.typography.fontFamily,
        lineHeight: tokens.typography.lineHeight.normal,
      },
      secondary: {
        color: tokens.colors["text-secondary"],
        fontFamily: tokens.typography.fontFamily,
        lineHeight: tokens.typography.lineHeight.normal,
      },
      muted: {
        color: tokens.colors["text-muted"],
        fontFamily: tokens.typography.fontFamily,
        lineHeight: tokens.typography.lineHeight.normal,
      },
      inverse: {
        color: tokens.colors["text-inverse"],
        fontFamily: tokens.typography.fontFamily,
        lineHeight: tokens.typography.lineHeight.normal,
      },
    },

    input: {
      base: {
        backgroundColor: tokens.colors.surface,
        borderColor: tokens.colors.border,
        borderRadius: tokens.borderRadius.md,
        padding: `${tokens.spacing["3"]} ${tokens.spacing["4"]}`,
        fontSize: tokens.typography.fontSize.base,
        color: tokens.colors.text,
        transition: tokens.transitions.normal,
        outline: "none",
        border: `1px solid ${tokens.colors.border}`,
        "&:focus": {
          borderColor: tokens.colors["border-focus"],
          boxShadow: `0 0 0 2px ${tokens.colors["border-focus"]}20`,
        },
        "&:hover": {
          borderColor: tokens.colors["border-hover"],
        },
      },
    },
  };
};
