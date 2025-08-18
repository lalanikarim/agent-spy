import React from "react";
import { useThemeColors } from "../../../hooks/useThemeStyles";

export interface ThemeIconProps {
  children: React.ReactNode;
  color?: string | "primary" | "secondary" | "success" | "warning" | "error" | "info" | "text" | "text-secondary" | "text-muted";
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  className?: string;
  style?: React.CSSProperties;
}

const ThemeIcon: React.FC<ThemeIconProps> = ({
  children,
  color = "text",
  size = "md",
  className = "",
  style = {},
}) => {
  const { getColor } = useThemeColors();
  
  const sizeStyles = {
    xs: { fontSize: "12px", width: "12px", height: "12px" },
    sm: { fontSize: "14px", width: "14px", height: "14px" },
    md: { fontSize: "16px", width: "16px", height: "16px" },
    lg: { fontSize: "20px", width: "20px", height: "20px" },
    xl: { fontSize: "24px", width: "24px", height: "24px" },
  };

  const iconColor = color.startsWith("#") ? color : getColor(color as any);

  const iconStyle = {
    ...sizeStyles[size],
    color: iconColor,
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
    ...style,
  };

  return (
    <span className={className} style={iconStyle}>
      {children}
    </span>
  );
};

export default ThemeIcon;
