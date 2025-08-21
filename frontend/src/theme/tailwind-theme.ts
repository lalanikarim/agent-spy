import { darkTokens, lightTokens } from "./tokens";

/**
 * Generate Tailwind theme configuration from our centralized theme tokens
 * This ensures consistency between our theme system and Tailwind
 */
export const generateTailwindTheme = () => {
  const light = lightTokens;
  // const dark = darkTokens;

  return {
    colors: {
      // Primary colors
      primary: {
        DEFAULT: light.colors.primary,
        hover: light.colors["primary-hover"],
        active: light.colors["primary-active"],
      },
      secondary: {
        DEFAULT: light.colors.secondary,
        hover: light.colors["secondary-hover"],
        active: light.colors["secondary-active"],
      },

      // Surface colors
      surface: {
        DEFAULT: light.colors.surface,
        hover: light.colors["surface-hover"],
        active: light.colors["surface-active"],
      },

      // Text colors
      text: {
        DEFAULT: light.colors.text,
        secondary: light.colors["text-secondary"],
        muted: light.colors["text-muted"],
        inverse: light.colors["text-inverse"],
      },

      // Border colors
      border: {
        DEFAULT: light.colors.border,
        hover: light.colors["border-hover"],
        focus: light.colors["border-focus"],
      },

      // Semantic colors
      success: {
        DEFAULT: light.colors.success,
        hover: light.colors["success-hover"],
      },
      warning: {
        DEFAULT: light.colors.warning,
        hover: light.colors["warning-hover"],
      },
      error: {
        DEFAULT: light.colors.error,
        hover: light.colors["error-hover"],
      },
      info: {
        DEFAULT: light.colors.info,
        hover: light.colors["info-hover"],
      },

      // Status colors
      status: {
        running: {
          bg: light.colors["status-running"],
          text: light.colors["status-running-text"],
        },
        completed: {
          bg: light.colors["status-completed"],
          text: light.colors["status-completed-text"],
        },
        failed: {
          bg: light.colors["status-failed"],
          text: light.colors["status-failed-text"],
        },
      },

      // Background colors
      background: {
        DEFAULT: light.colors.background,
        surface: light.colors.surface,
        "surface-hover": light.colors["surface-hover"],
        "surface-active": light.colors["surface-active"],
      },
    },

    // Typography
    fontFamily: {
      theme: light.typography.fontFamily,
    },

    fontSize: {
      "theme-xs": light.typography.fontSize.xs,
      "theme-sm": light.typography.fontSize.sm,
      "theme-base": light.typography.fontSize.base,
      "theme-lg": light.typography.fontSize.lg,
      "theme-xl": light.typography.fontSize.xl,
      "theme-2xl": light.typography.fontSize["2xl"],
      "theme-3xl": light.typography.fontSize["3xl"],
    },

    fontWeight: {
      "theme-normal": light.typography.fontWeight.normal,
      "theme-medium": light.typography.fontWeight.medium,
      "theme-semibold": light.typography.fontWeight.semibold,
      "theme-bold": light.typography.fontWeight.bold,
    },

    lineHeight: {
      "theme-tight": light.typography.lineHeight.tight,
      "theme-normal": light.typography.lineHeight.normal,
      "theme-relaxed": light.typography.lineHeight.relaxed,
    },

    // Spacing
    spacing: {
      "theme-1": light.spacing["1"],
      "theme-2": light.spacing["2"],
      "theme-3": light.spacing["3"],
      "theme-4": light.spacing["4"],
      "theme-5": light.spacing["5"],
      "theme-6": light.spacing["6"],
      "theme-8": light.spacing["8"],
      "theme-10": light.spacing["10"],
      "theme-12": light.spacing["12"],
    },

    // Shadows
    boxShadow: {
      "theme-sm": light.shadows.sm,
      "theme-md": light.shadows.md,
      "theme-lg": light.shadows.lg,
      "theme-xl": light.shadows.xl,
    },

    // Border radius
    borderRadius: {
      "theme-sm": light.borderRadius.sm,
      "theme-md": light.borderRadius.md,
      "theme-lg": light.borderRadius.lg,
      "theme-xl": light.borderRadius.xl,
      "theme-full": light.borderRadius.full,
    },

    // Transitions
    transitionDuration: {
      "theme-fast": light.transitions.fast.replace("ms ease-in-out", "ms"),
      "theme-normal": light.transitions.normal.replace("ms ease-in-out", "ms"),
      "theme-slow": light.transitions.slow.replace("ms ease-in-out", "ms"),
    },

    // Z-index
    zIndex: {
      "theme-dropdown": light.zIndex.dropdown,
      "theme-sticky": light.zIndex.sticky,
      "theme-fixed": light.zIndex.fixed,
      "theme-modal-backdrop": light.zIndex["modal-backdrop"],
      "theme-modal": light.zIndex.modal,
      "theme-popover": light.zIndex.popover,
      "theme-tooltip": light.zIndex.tooltip,
      "theme-toast": light.zIndex.toast,
    },

    // Animations
    animation: {
      "fade-in": "fadeIn var(--transition-normal) ease-out",
      "slide-in": "slideIn var(--transition-normal) ease-out",
      "pulse-slow": "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
    },

    // Backdrop blur
    backdropBlur: {
      theme: "10px",
    },
  };
};

/**
 * Generate CSS custom properties for both light and dark themes
 * This replaces the manual CSS variables in theme.css
 */
export const generateCSSVariables = () => {
  const light = lightTokens;
  const dark = darkTokens;

  const lightVars = Object.entries(light).flatMap(([category, values]) => {
    return Object.entries(values).map(([key, value]) => {
      // Use correct naming convention: --color-* for colors, --* for others
      const cssVarName =
        category === "colors" ? `--color-${key}` : `--${category}-${key}`;
      return `${cssVarName}: ${value};`;
    });
  });

  const darkVars = Object.entries(dark).flatMap(([category, values]) => {
    return Object.entries(values).map(([key, value]) => {
      // Use correct naming convention: --color-* for colors, --* for others
      const cssVarName =
        category === "colors" ? `--color-${key}` : `--${category}-${key}`;
      return `${cssVarName}: ${value};`;
    });
  });

  return {
    light: lightVars.join("\n  "),
    dark: darkVars.join("\n  "),
  };
};

/**
 * Generate optimized CSS that uses our theme tokens
 */
export const generateOptimizedCSS = () => {
  const vars = generateCSSVariables();

  return `/* Theme System - Generated from centralized tokens */

/* Light Theme Variables */
:root {
  ${vars.light}
}

/* Dark Theme Variables */
[data-theme="dark"] {
  ${vars.dark}
}

/* Utility Classes */
.bg-theme-surface { background-color: var(--color-surface); }
.bg-theme-surface-hover { background-color: var(--color-surface-hover); }
.bg-theme-surface-active { background-color: var(--color-surface-active); }

.text-theme-text { color: var(--color-text); }
.text-theme-text-secondary { color: var(--color-text-secondary); }
.text-theme-text-muted { color: var(--color-text-muted); }
.text-theme-text-inverse { color: var(--color-text-inverse); }

.border-theme-border { border-color: var(--color-border); }
.border-theme-border-hover { border-color: var(--color-border-hover); }
.border-theme-border-focus { border-color: var(--color-border-focus); }

/* Dedicated hover utility classes */
.bg-theme-hover-light { background-color: var(--color-hover-light); }
.bg-theme-hover-dark { background-color: var(--color-hover-dark); }
.text-theme-hover-text { color: var(--color-hover-text); }
.border-theme-hover-border { border-color: var(--color-hover-border); }

/* Dedicated selection utility classes */
.bg-theme-selection-light { background-color: var(--color-selection-light); }
.bg-theme-selection-dark { background-color: var(--color-selection-dark); }
.text-theme-selection-text-light { color: var(--color-selection-text-light); }
.text-theme-selection-text-dark { color: var(--color-selection-text-dark); }

.shadow-theme-sm { box-shadow: var(--shadows-sm); }
.shadow-theme-md { box-shadow: var(--shadows-md); }
.shadow-theme-lg { box-shadow: var(--shadows-lg); }
.shadow-theme-xl { box-shadow: var(--shadows-xl); }

.rounded-theme-sm { border-radius: var(--borderRadius-sm); }
.rounded-theme-md { border-radius: var(--borderRadius-md); }
.rounded-theme-lg { border-radius: var(--borderRadius-lg); }
.rounded-theme-xl { border-radius: var(--borderRadius-xl); }

.transition-theme-fast { transition-duration: var(--transitions-fast); }
.transition-theme-normal { transition-duration: var(--transitions-normal); }
.transition-theme-slow { transition-duration: var(--transitions-slow); }

/* Ant Design Overrides */
.ant-btn {
  border-radius: var(--borderRadius-md);
  transition: all var(--transitions-normal);
}

.ant-card {
  border-radius: var(--borderRadius-lg);
  box-shadow: var(--shadows-md);
}

.ant-input {
  border-radius: var(--borderRadius-md);
  transition: all var(--transitions-normal);
}

.ant-select {
  border-radius: var(--borderRadius-md);
}

.ant-modal {
  border-radius: var(--borderRadius-lg);
}

/* Animation Keyframes */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideIn {
  from { transform: translateY(-10px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}`;
};
