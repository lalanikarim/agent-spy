import React from "react";
import { useThemeStyleObjects } from "../../../hooks/useThemeStyles";

export interface ThemeCardProps {
  children: React.ReactNode;
  variant?: "default" | "elevated" | "interactive";
  padding?: "none" | "small" | "medium" | "large";
  hover?: boolean;
  onClick?: () => void;
  className?: string;
  style?: React.CSSProperties;
}

const ThemeCard: React.FC<ThemeCardProps> = ({
  children,
  variant = "default",
  padding = "medium",
  hover = false,
  onClick,
  className = "",
  style = {},
}) => {
  const styles = useThemeStyleObjects();

  const paddingStyles = {
    none: { padding: "0" },
    small: { padding: "12px" },
    medium: { padding: "16px" },
    large: { padding: "24px" },
  };

  const variantStyles = {
    default: {
      ...styles.card.base,
    },
    elevated: {
      ...styles.card.base,
      boxShadow: styles.card.base.boxShadow,
    },
    interactive: {
      ...styles.card.base,
      cursor: onClick ? "pointer" : "default",
      transition: "all 0.2s ease-in-out",
    },
  };

  const cardStyle = {
    ...variantStyles[variant],
    ...paddingStyles[padding],
    ...style,
  };

  const handleClick = () => {
    if (onClick && variant === "interactive") {
      onClick();
    }
  };

  const handleMouseEnter = (e: React.MouseEvent) => {
    if (hover && variant === "interactive") {
      // Only apply shadow hover effect, keep background subtle
      (e.currentTarget as HTMLElement).style.boxShadow = styles.card.hover.boxShadow;
    }
  };

  const handleMouseLeave = (e: React.MouseEvent) => {
    if (hover && variant === "interactive") {
      // Restore original shadow
      (e.currentTarget as HTMLElement).style.boxShadow = styles.card.base.boxShadow;
    }
  };

  return (
    <div
      className={className}
      style={cardStyle}
      onClick={handleClick}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {children}
    </div>
  );
};

export default ThemeCard;
