import { MoonFilled, SunFilled } from "@ant-design/icons";
import { Button, Tooltip } from "antd";
import React from "react";
import { useTheme } from "../contexts/ThemeContext";

interface ThemeToggleProps {
  size?: "small" | "middle" | "large";
  showLabel?: boolean;
  className?: string;
}

const ThemeToggle: React.FC<ThemeToggleProps> = ({
  size = "middle",
  showLabel = false,
  className = "",
}) => {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  const buttonSize = {
    small: "w-8 h-8",
    middle: "w-10 h-10",
    large: "w-12 h-12",
  };

  const iconSize = {
    small: 14,
    middle: 16,
    large: 18,
  };

  return (
    <Tooltip
      title={`Switch to ${isDark ? "light" : "dark"} mode`}
      placement="bottom"
    >
      <Button
        type="text"
        icon={
          isDark ? (
            <SunFilled
              style={{
                color: "var(--color-yellow-500)",
                fontSize: iconSize[size],
              }}
            />
          ) : (
            <MoonFilled
              style={{
                color: "var(--color-gray-300)",
                fontSize: iconSize[size],
              }}
            />
          )
        }
        onClick={toggleTheme}
        className={`
          ${buttonSize[size]}
          flex items-center justify-center
          rounded-full
          transition-all duration-200
          ${className}
        `}
        style={{
          minWidth: "auto",
          padding: 0,
          backgroundColor: "var(--color-surface)",
          border: "1px solid var(--color-border)",
          color: "var(--color-text)",
        }}
      >
        {showLabel && (
          <span className="ml-2 font-medium">{isDark ? "Light" : "Dark"}</span>
        )}
      </Button>
    </Tooltip>
  );
};

export default ThemeToggle;
