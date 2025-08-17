import React from 'react';
import { Button, Tooltip } from 'antd';
import { SunOutlined, MoonOutlined } from '@ant-design/icons';
import { useTheme } from '../contexts/ThemeContext';

interface ThemeToggleProps {
  size?: 'small' | 'middle' | 'large';
  showLabel?: boolean;
  className?: string;
}

const ThemeToggle: React.FC<ThemeToggleProps> = ({ 
  size = 'middle', 
  showLabel = false,
  className = ''
}) => {
  const { theme, toggleTheme } = useTheme();

  const isDark = theme === 'dark';

  const buttonSize = {
    small: 'w-8 h-8',
    middle: 'w-10 h-10',
    large: 'w-12 h-12'
  };

  const iconSize = {
    small: 14,
    middle: 16,
    large: 18
  };

  return (
    <Tooltip 
      title={`Switch to ${isDark ? 'light' : 'dark'} mode`}
      placement="bottom"
    >
      <Button
        type="text"
        icon={
          <div className="relative">
            {/* Sun Icon */}
            <SunOutlined 
              size={iconSize[size]}
              className={`absolute inset-0 transition-all duration-theme-normal ${
                isDark 
                  ? 'opacity-0 rotate-90 scale-75' 
                  : 'opacity-100 rotate-0 scale-100'
              }`}
              style={{ color: 'var(--color-warning)' }}
            />
            {/* Moon Icon */}
            <MoonOutlined 
              size={iconSize[size]}
              className={`absolute inset-0 transition-all duration-theme-normal ${
                isDark 
                  ? 'opacity-100 rotate-0 scale-100' 
                  : 'opacity-0 -rotate-90 scale-75'
              }`}
              style={{ color: 'var(--color-secondary)' }}
            />
          </div>
        }
        onClick={toggleTheme}
        className={`
          ${buttonSize[size]}
          flex items-center justify-center
          bg-surface hover:bg-surface-hover
          border border-border hover:border-border-hover
          rounded-theme-full
          transition-all duration-theme-normal
          hover:shadow-theme-md
          focus:outline-none focus:ring-2 focus:ring-border-focus focus:ring-opacity-50
          ${className}
        `}
        style={{
          minWidth: 'auto',
          padding: 0,
        }}
      >
        {showLabel && (
          <span className="ml-2 text-text font-theme-medium">
            {isDark ? 'Light' : 'Dark'}
          </span>
        )}
      </Button>
    </Tooltip>
  );
};

export default ThemeToggle;
