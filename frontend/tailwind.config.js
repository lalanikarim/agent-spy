/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Theme-aware colors using CSS variables
        primary: {
          DEFAULT: 'var(--color-primary)',
          hover: 'var(--color-primary-hover)',
          active: 'var(--color-primary-active)',
        },
        secondary: {
          DEFAULT: 'var(--color-secondary)',
          hover: 'var(--color-secondary-hover)',
          active: 'var(--color-secondary-active)',
        },
        surface: {
          DEFAULT: 'var(--color-surface)',
          hover: 'var(--color-surface-hover)',
          active: 'var(--color-surface-active)',
        },
        text: {
          DEFAULT: 'var(--color-text)',
          secondary: 'var(--color-text-secondary)',
          muted: 'var(--color-text-muted)',
          inverse: 'var(--color-text-inverse)',
        },
        border: {
          DEFAULT: 'var(--color-border)',
          hover: 'var(--color-border-hover)',
          focus: 'var(--color-border-focus)',
        },
        success: {
          DEFAULT: 'var(--color-success)',
          hover: 'var(--color-success-hover)',
        },
        warning: {
          DEFAULT: 'var(--color-warning)',
          hover: 'var(--color-warning-hover)',
        },
        error: {
          DEFAULT: 'var(--color-error)',
          hover: 'var(--color-error-hover)',
        },
        info: {
          DEFAULT: 'var(--color-info)',
          hover: 'var(--color-info-hover)',
        },
        status: {
          running: {
            bg: 'var(--color-status-running)',
            text: 'var(--color-status-running-text)',
          },
          completed: {
            bg: 'var(--color-status-completed)',
            text: 'var(--color-status-completed-text)',
          },
          failed: {
            bg: 'var(--color-status-failed)',
            text: 'var(--color-status-failed-text)',
          },
        },
      },
      backgroundColor: {
        theme: 'var(--color-background)',
        surface: 'var(--color-surface)',
        'surface-hover': 'var(--color-surface-hover)',
        'surface-active': 'var(--color-surface-active)',
      },
      textColor: {
        theme: 'var(--color-text)',
        'theme-secondary': 'var(--color-text-secondary)',
        'theme-muted': 'var(--color-text-muted)',
        'theme-inverse': 'var(--color-text-inverse)',
      },
      borderColor: {
        theme: 'var(--color-border)',
        'theme-hover': 'var(--color-border-hover)',
        'theme-focus': 'var(--color-border-focus)',
      },
      boxShadow: {
        'theme-sm': 'var(--shadow-sm)',
        'theme-md': 'var(--shadow-md)',
        'theme-lg': 'var(--shadow-lg)',
        'theme-xl': 'var(--shadow-xl)',
      },
      borderRadius: {
        'theme-sm': 'var(--radius-sm)',
        'theme-md': 'var(--radius-md)',
        'theme-lg': 'var(--radius-lg)',
        'theme-xl': 'var(--radius-xl)',
      },
      fontFamily: {
        theme: 'var(--font-family)',
      },
      fontSize: {
        'theme-xs': 'var(--font-size-xs)',
        'theme-sm': 'var(--font-size-sm)',
        'theme-base': 'var(--font-size-base)',
        'theme-lg': 'var(--font-size-lg)',
        'theme-xl': 'var(--font-size-xl)',
        'theme-2xl': 'var(--font-size-2xl)',
        'theme-3xl': 'var(--font-size-3xl)',
      },
      fontWeight: {
        'theme-normal': 'var(--font-weight-normal)',
        'theme-medium': 'var(--font-weight-medium)',
        'theme-semibold': 'var(--font-weight-semibold)',
        'theme-bold': 'var(--font-weight-bold)',
      },
      lineHeight: {
        'theme-tight': 'var(--line-height-tight)',
        'theme-normal': 'var(--line-height-normal)',
        'theme-relaxed': 'var(--line-height-relaxed)',
      },
      spacing: {
        'theme-1': 'var(--space-1)',
        'theme-2': 'var(--space-2)',
        'theme-3': 'var(--space-3)',
        'theme-4': 'var(--space-4)',
        'theme-5': 'var(--space-5)',
        'theme-6': 'var(--space-6)',
        'theme-8': 'var(--space-8)',
        'theme-10': 'var(--space-10)',
        'theme-12': 'var(--space-12)',
      },
      transitionDuration: {
        'theme-fast': 'var(--transition-fast)',
        'theme-normal': 'var(--transition-normal)',
        'theme-slow': 'var(--transition-slow)',
      },
      zIndex: {
        'theme-dropdown': 'var(--z-dropdown)',
        'theme-sticky': 'var(--z-sticky)',
        'theme-fixed': 'var(--z-fixed)',
        'theme-modal-backdrop': 'var(--z-modal-backdrop)',
        'theme-modal': 'var(--z-modal)',
        'theme-popover': 'var(--z-popover)',
        'theme-tooltip': 'var(--z-tooltip)',
        'theme-toast': 'var(--z-toast)',
      },
      animation: {
        'fade-in': 'fadeIn var(--transition-normal) ease-out',
        'slide-in': 'slideIn var(--transition-normal) ease-out',
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      backdropBlur: {
        'theme': '10px',
      },
    },
  },
  plugins: [],
  corePlugins: {
    // Disable Tailwind's preflight to avoid conflicts with Ant Design
    preflight: false,
  }
}
