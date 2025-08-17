/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Light mode colors
        primary: {
          DEFAULT: '#3b82f6',
          hover: '#2563eb',
          active: '#1d4ed8',
        },
        secondary: {
          DEFAULT: '#6366f1',
          hover: '#5855eb',
          active: '#4f46e5',
        },
        surface: {
          DEFAULT: '#ffffff',
          hover: '#f1f5f9',
          active: '#e2e8f0',
        },
        text: {
          DEFAULT: '#1e293b',
          secondary: '#64748b',
          muted: '#94a3b8',
          inverse: '#ffffff',
        },
        border: {
          DEFAULT: '#e2e8f0',
          hover: '#cbd5e1',
          focus: '#3b82f6',
        },
        success: {
          DEFAULT: '#10b981',
          hover: '#059669',
        },
        warning: {
          DEFAULT: '#f59e0b',
          hover: '#d97706',
        },
        error: {
          DEFAULT: '#ef4444',
          hover: '#dc2626',
        },
        info: {
          DEFAULT: '#3b82f6',
          hover: '#2563eb',
        },
        status: {
          running: {
            bg: '#e6f7ff',
            text: '#1890ff',
          },
          completed: {
            bg: '#f6ffed',
            text: '#52c41a',
          },
          failed: {
            bg: '#fff2f0',
            text: '#ff4d4f',
          },
        },
      },
      backgroundColor: {
        theme: '#f8fafc',
        surface: '#ffffff',
        'surface-hover': '#f1f5f9',
        'surface-active': '#e2e8f0',
      },
      textColor: {
        theme: '#1e293b',
        'theme-secondary': '#64748b',
        'theme-muted': '#94a3b8',
        'theme-inverse': '#ffffff',
      },
      borderColor: {
        theme: '#f1f5f9',
        'theme-hover': '#e2e8f0',
        'theme-focus': '#3b82f6',
      },
      boxShadow: {
        'theme-sm': '0 1px 2px 0 rgb(0 0 0 / 0.05)',
        'theme-md': '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
        'theme-lg': '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
        'theme-xl': '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
      },
      borderRadius: {
        'theme-sm': '4px',
        'theme-md': '8px',
        'theme-lg': '12px',
        'theme-xl': '16px',
      },
      fontFamily: {
        theme: 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      },
      fontSize: {
        'theme-xs': '12px',
        'theme-sm': '14px',
        'theme-base': '16px',
        'theme-lg': '18px',
        'theme-xl': '20px',
        'theme-2xl': '24px',
        'theme-3xl': '30px',
      },
      fontWeight: {
        'theme-normal': '400',
        'theme-medium': '500',
        'theme-semibold': '600',
        'theme-bold': '700',
      },
      lineHeight: {
        'theme-tight': '1.25',
        'theme-normal': '1.5',
        'theme-relaxed': '1.6',
      },
      spacing: {
        'theme-1': '4px',
        'theme-2': '8px',
        'theme-3': '12px',
        'theme-4': '16px',
        'theme-5': '20px',
        'theme-6': '24px',
        'theme-8': '32px',
        'theme-10': '40px',
        'theme-12': '48px',
      },
      transitionDuration: {
        'theme-fast': '150ms',
        'theme-normal': '250ms',
        'theme-slow': '350ms',
      },
      zIndex: {
        'theme-dropdown': '1000',
        'theme-sticky': '1020',
        'theme-fixed': '1030',
        'theme-modal-backdrop': '1040',
        'theme-modal': '1050',
        'theme-popover': '1060',
        'theme-tooltip': '1070',
        'theme-toast': '1080',
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
}
