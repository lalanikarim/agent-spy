import type { Theme } from "./tokens";
import { getThemeTokens } from "./tokens";

/**
 * Theme variants for common use cases
 * Provides predefined style combinations that can be easily applied
 */
export const createThemeVariants = (theme: Theme) => {
  const tokens = getThemeTokens(theme);

  return {
    // Card variants
    card: {
      default: {
        backgroundColor: tokens.colors.surface,
        borderColor: tokens.colors.border,
        borderRadius: tokens.borderRadius.lg,
        boxShadow: tokens.shadows.md,
        transition: tokens.transitions.normal,
        border: `1px solid ${tokens.colors.border}`,
      },

      elevated: {
        backgroundColor: tokens.colors.surface,
        borderColor: tokens.colors.border,
        borderRadius: tokens.borderRadius.lg,
        boxShadow: tokens.shadows.lg,
        transition: tokens.transitions.normal,
        border: `1px solid ${tokens.colors.border}`,
      },

      interactive: {
        backgroundColor: tokens.colors.surface,
        borderColor: tokens.colors.border,
        borderRadius: tokens.borderRadius.lg,
        boxShadow: tokens.shadows.md,
        transition: tokens.transitions.normal,
        border: `1px solid ${tokens.colors.border}`,
        cursor: "pointer",
        "&:hover": {
          backgroundColor: tokens.colors["surface-hover"],
          borderColor: tokens.colors["border-hover"],
          boxShadow: tokens.shadows.lg,
        },
        "&:active": {
          backgroundColor: tokens.colors["surface-active"],
          borderColor: tokens.colors["border-hover"],
        },
      },

      glass: {
        backgroundColor:
          theme === "light"
            ? "rgba(255, 255, 255, 0.8)"
            : "rgba(30, 41, 59, 0.8)",
        backdropFilter: "blur(10px)",
        borderColor:
          theme === "light"
            ? "rgba(255, 255, 255, 0.2)"
            : "rgba(51, 65, 85, 0.3)",
        borderRadius: tokens.borderRadius.lg,
        boxShadow: tokens.shadows.md,
        transition: tokens.transitions.normal,
        border: `1px solid ${
          theme === "light"
            ? "rgba(255, 255, 255, 0.2)"
            : "rgba(51, 65, 85, 0.3)"
        }`,
      },

      outline: {
        backgroundColor: "transparent",
        borderColor: tokens.colors.border,
        borderRadius: tokens.borderRadius.lg,
        transition: tokens.transitions.normal,
        border: `2px solid ${tokens.colors.border}`,
        "&:hover": {
          borderColor: tokens.colors["border-hover"],
          backgroundColor: tokens.colors["surface-hover"],
        },
      },
    },

    // Button variants
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
        "&:disabled": {
          backgroundColor: tokens.colors["text-muted"],
          borderColor: tokens.colors["text-muted"],
          cursor: "not-allowed",
          opacity: 0.6,
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
        "&:disabled": {
          backgroundColor: tokens.colors["text-muted"],
          borderColor: tokens.colors["text-muted"],
          cursor: "not-allowed",
          opacity: 0.6,
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
        "&:active": {
          backgroundColor: tokens.colors["surface-active"],
          color: tokens.colors.text,
        },
        "&:disabled": {
          color: tokens.colors["text-muted"],
          cursor: "not-allowed",
          opacity: 0.6,
        },
      },

      outline: {
        backgroundColor: "transparent",
        color: tokens.colors.primary,
        borderColor: tokens.colors.primary,
        borderRadius: tokens.borderRadius.md,
        transition: tokens.transitions.normal,
        padding: `${tokens.spacing["3"]} ${tokens.spacing["4"]}`,
        fontSize: tokens.typography.fontSize.base,
        fontWeight: tokens.typography.fontWeight.medium,
        cursor: "pointer",
        border: `1px solid ${tokens.colors.primary}`,
        outline: "none",
        "&:hover": {
          backgroundColor: tokens.colors.primary,
          color: tokens.colors["text-inverse"],
        },
        "&:active": {
          backgroundColor: tokens.colors["primary-active"],
          borderColor: tokens.colors["primary-active"],
          color: tokens.colors["text-inverse"],
        },
        "&:disabled": {
          color: tokens.colors["text-muted"],
          borderColor: tokens.colors["text-muted"],
          cursor: "not-allowed",
          opacity: 0.6,
        },
      },

      danger: {
        backgroundColor: tokens.colors.error,
        color: tokens.colors["text-inverse"],
        borderColor: tokens.colors.error,
        borderRadius: tokens.borderRadius.md,
        transition: tokens.transitions.normal,
        padding: `${tokens.spacing["3"]} ${tokens.spacing["4"]}`,
        fontSize: tokens.typography.fontSize.base,
        fontWeight: tokens.typography.fontWeight.medium,
        cursor: "pointer",
        border: "none",
        outline: "none",
        "&:hover": {
          backgroundColor: tokens.colors["error-hover"],
          borderColor: tokens.colors["error-hover"],
        },
        "&:active": {
          backgroundColor: tokens.colors["error-hover"],
          borderColor: tokens.colors["error-hover"],
        },
        "&:disabled": {
          backgroundColor: tokens.colors["text-muted"],
          borderColor: tokens.colors["text-muted"],
          cursor: "not-allowed",
          opacity: 0.6,
        },
      },
    },

    // Text variants
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

      success: {
        color: tokens.colors.success,
        fontFamily: tokens.typography.fontFamily,
        lineHeight: tokens.typography.lineHeight.normal,
      },

      warning: {
        color: tokens.colors.warning,
        fontFamily: tokens.typography.fontFamily,
        lineHeight: tokens.typography.lineHeight.normal,
      },

      error: {
        color: tokens.colors.error,
        fontFamily: tokens.typography.fontFamily,
        lineHeight: tokens.typography.lineHeight.normal,
      },

      info: {
        color: tokens.colors.info,
        fontFamily: tokens.typography.fontFamily,
        lineHeight: tokens.typography.lineHeight.normal,
      },
    },

    // Input variants
    input: {
      default: {
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
        "&:disabled": {
          backgroundColor: tokens.colors["surface-hover"],
          color: tokens.colors["text-muted"],
          cursor: "not-allowed",
          opacity: 0.6,
        },
      },

      error: {
        backgroundColor: tokens.colors.surface,
        borderColor: tokens.colors.error,
        borderRadius: tokens.borderRadius.md,
        padding: `${tokens.spacing["3"]} ${tokens.spacing["4"]}`,
        fontSize: tokens.typography.fontSize.base,
        color: tokens.colors.text,
        transition: tokens.transitions.normal,
        outline: "none",
        border: `1px solid ${tokens.colors.error}`,
        "&:focus": {
          borderColor: tokens.colors.error,
          boxShadow: `0 0 0 2px ${tokens.colors.error}20`,
        },
        "&:hover": {
          borderColor: tokens.colors["error-hover"],
        },
      },

      success: {
        backgroundColor: tokens.colors.surface,
        borderColor: tokens.colors.success,
        borderRadius: tokens.borderRadius.md,
        padding: `${tokens.spacing["3"]} ${tokens.spacing["4"]}`,
        fontSize: tokens.typography.fontSize.base,
        color: tokens.colors.text,
        transition: tokens.transitions.normal,
        outline: "none",
        border: `1px solid ${tokens.colors.success}`,
        "&:focus": {
          borderColor: tokens.colors.success,
          boxShadow: `0 0 0 2px ${tokens.colors.success}20`,
        },
        "&:hover": {
          borderColor: tokens.colors["success-hover"],
        },
      },
    },

    // Badge variants
    badge: {
      default: {
        backgroundColor: tokens.colors["surface-hover"],
        color: tokens.colors["text-secondary"],
        borderRadius: tokens.borderRadius.full,
        padding: `${tokens.spacing["1"]} ${tokens.spacing["2"]}`,
        fontSize: tokens.typography.fontSize.xs,
        fontWeight: tokens.typography.fontWeight.medium,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
      },

      primary: {
        backgroundColor: tokens.colors.primary,
        color: tokens.colors["text-inverse"],
        borderRadius: tokens.borderRadius.full,
        padding: `${tokens.spacing["1"]} ${tokens.spacing["2"]}`,
        fontSize: tokens.typography.fontSize.xs,
        fontWeight: tokens.typography.fontWeight.medium,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
      },

      success: {
        backgroundColor: tokens.colors.success,
        color: tokens.colors["text-inverse"],
        borderRadius: tokens.borderRadius.full,
        padding: `${tokens.spacing["1"]} ${tokens.spacing["2"]}`,
        fontSize: tokens.typography.fontSize.xs,
        fontWeight: tokens.typography.fontWeight.medium,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
      },

      warning: {
        backgroundColor: tokens.colors.warning,
        color: tokens.colors["text-inverse"],
        borderRadius: tokens.borderRadius.full,
        padding: `${tokens.spacing["1"]} ${tokens.spacing["2"]}`,
        fontSize: tokens.typography.fontSize.xs,
        fontWeight: tokens.typography.fontWeight.medium,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
      },

      error: {
        backgroundColor: tokens.colors.error,
        color: tokens.colors["text-inverse"],
        borderRadius: tokens.borderRadius.full,
        padding: `${tokens.spacing["1"]} ${tokens.spacing["2"]}`,
        fontSize: tokens.typography.fontSize.xs,
        fontWeight: tokens.typography.fontWeight.medium,
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
      },
    },

    // Status variants
    status: {
      running: {
        backgroundColor: tokens.colors["status-running"],
        color: tokens.colors["status-running-text"],
        borderRadius: tokens.borderRadius.md,
        padding: `${tokens.spacing["2"]} ${tokens.spacing["3"]}`,
        fontSize: tokens.typography.fontSize.sm,
        fontWeight: tokens.typography.fontWeight.medium,
        display: "inline-flex",
        alignItems: "center",
        gap: tokens.spacing["2"],
      },

      completed: {
        backgroundColor: tokens.colors["status-completed"],
        color: tokens.colors["status-completed-text"],
        borderRadius: tokens.borderRadius.md,
        padding: `${tokens.spacing["2"]} ${tokens.spacing["3"]}`,
        fontSize: tokens.typography.fontSize.sm,
        fontWeight: tokens.typography.fontWeight.medium,
        display: "inline-flex",
        alignItems: "center",
        gap: tokens.spacing["2"],
      },

      failed: {
        backgroundColor: tokens.colors["status-failed"],
        color: tokens.colors["status-failed-text"],
        borderRadius: tokens.borderRadius.md,
        padding: `${tokens.spacing["2"]} ${tokens.spacing["3"]}`,
        fontSize: tokens.typography.fontSize.sm,
        fontWeight: tokens.typography.fontWeight.medium,
        display: "inline-flex",
        alignItems: "center",
        gap: tokens.spacing["2"],
      },
    },

    // Icon variants
    icon: {
      default: {
        color: tokens.colors["text-secondary"],
        fontSize: tokens.typography.fontSize.base,
        transition: tokens.transitions.normal,
      },

      primary: {
        color: tokens.colors.primary,
        fontSize: tokens.typography.fontSize.base,
        transition: tokens.transitions.normal,
      },

      secondary: {
        color: tokens.colors.secondary,
        fontSize: tokens.typography.fontSize.base,
        transition: tokens.transitions.normal,
      },

      success: {
        color: tokens.colors.success,
        fontSize: tokens.typography.fontSize.base,
        transition: tokens.transitions.normal,
      },

      warning: {
        color: tokens.colors.warning,
        fontSize: tokens.typography.fontSize.base,
        transition: tokens.transitions.normal,
      },

      error: {
        color: tokens.colors.error,
        fontSize: tokens.typography.fontSize.base,
        transition: tokens.transitions.normal,
      },

      info: {
        color: tokens.colors.info,
        fontSize: tokens.typography.fontSize.base,
        transition: tokens.transitions.normal,
      },

      muted: {
        color: tokens.colors["text-muted"],
        fontSize: tokens.typography.fontSize.base,
        transition: tokens.transitions.normal,
      },

      inverse: {
        color: tokens.colors["text-inverse"],
        fontSize: tokens.typography.fontSize.base,
        transition: tokens.transitions.normal,
      },

      // Status-specific icon colors
      statusRunning: {
        color: tokens.colors.info,
        fontSize: tokens.typography.fontSize.base,
        transition: tokens.transitions.normal,
      },

      statusCompleted: {
        color: tokens.colors.success,
        fontSize: tokens.typography.fontSize.base,
        transition: tokens.transitions.normal,
      },

      statusFailed: {
        color: tokens.colors.error,
        fontSize: tokens.typography.fontSize.base,
        transition: tokens.transitions.normal,
      },

      // Badge-specific icon colors
      badgeDefault: {
        color: tokens.colors["text-secondary"],
        fontSize: tokens.typography.fontSize.xs,
        transition: tokens.transitions.normal,
      },

      badgePrimary: {
        color: tokens.colors["text-inverse"],
        fontSize: tokens.typography.fontSize.xs,
        transition: tokens.transitions.normal,
      },

      badgeSuccess: {
        color: tokens.colors["text-inverse"],
        fontSize: tokens.typography.fontSize.xs,
        transition: tokens.transitions.normal,
      },

      badgeWarning: {
        color: tokens.colors["text-inverse"],
        fontSize: tokens.typography.fontSize.xs,
        transition: tokens.transitions.normal,
      },

      badgeError: {
        color: tokens.colors["text-inverse"],
        fontSize: tokens.typography.fontSize.xs,
        transition: tokens.transitions.normal,
      },
    },
  };
};

/**
 * Utility function to get a specific variant
 */
export const getVariant = (
  theme: Theme,
  component: string,
  variant: string
) => {
  const variants = createThemeVariants(theme);
  return variants[component as keyof typeof variants]?.[variant as any] || {};
};

/**
 * Utility function to merge variants
 */
export const mergeVariants = (
  theme: Theme,
  component: string,
  variants: string[]
) => {
  const allVariants = createThemeVariants(theme);
  const componentVariants = allVariants[component as keyof typeof allVariants];

  if (!componentVariants) return {};

  return variants.reduce((merged, variant) => {
    const variantStyles = componentVariants[variant as any];
    return { ...merged, ...variantStyles };
  }, {});
};
