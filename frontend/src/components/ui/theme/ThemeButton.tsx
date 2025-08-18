import React from "react";
import { useThemeStyleObjects } from "../../../hooks/useThemeStyles";

export interface ThemeButtonProps {
  children: React.ReactNode;
  variant?: "primary" | "secondary" | "ghost";
  size?: "small" | "medium" | "large";
  disabled?: boolean;
  onClick?: () => void;
  className?: string;
  type?: "button" | "submit" | "reset";
}

const ThemeButton: React.FC<ThemeButtonProps> = ({
  children,
  variant = "primary",
  size = "medium",
  disabled = false,
  onClick,
  className = "",
  type = "button",
}) => {
  const styles = useThemeStyleObjects();
  
  const sizeStyles = {
    small: {
      padding: "6px 12px",
      fontSize: "12px",
    },
    medium: {
      padding: "8px 16px",
      fontSize: "14px",
    },
    large: {
      padding: "12px 24px",
      fontSize: "16px",
    },
  };

  const buttonStyle = {
    ...styles.button[variant],
    ...sizeStyles[size],
    cursor: disabled ? "not-allowed" : "pointer",
    opacity: disabled ? 0.6 : 1,
    border: "none",
    outline: "none",
    fontFamily: "inherit",
    fontWeight: 500,
  };

  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={className}
      style={buttonStyle}
    >
      {children}
    </button>
  );
};

export default ThemeButton;
