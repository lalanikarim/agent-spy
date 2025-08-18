import React from "react";
import { useThemeStyleObjects } from "../../../hooks/useThemeStyles";

export interface ThemeTextProps {
  children: React.ReactNode;
  variant?: "primary" | "secondary" | "muted" | "inverse";
  size?: "xs" | "sm" | "base" | "lg" | "xl" | "2xl" | "3xl";
  weight?: "normal" | "medium" | "semibold" | "bold";
  as?: "span" | "p" | "div" | "h1" | "h2" | "h3" | "h4" | "h5" | "h6";
  className?: string;
  style?: React.CSSProperties;
}

const ThemeText: React.FC<ThemeTextProps> = ({
  children,
  variant = "primary",
  size = "base",
  weight = "normal",
  as = "span",
  className = "",
  style = {},
}) => {
  const styles = useThemeStyleObjects();

  const sizeStyles = {
    xs: { fontSize: "12px", lineHeight: "16px" },
    sm: { fontSize: "14px", lineHeight: "20px" },
    base: { fontSize: "16px", lineHeight: "24px" },
    lg: { fontSize: "18px", lineHeight: "28px" },
    xl: { fontSize: "20px", lineHeight: "28px" },
    "2xl": { fontSize: "24px", lineHeight: "32px" },
    "3xl": { fontSize: "30px", lineHeight: "36px" },
  };

  const weightStyles = {
    normal: { fontWeight: 400 },
    medium: { fontWeight: 500 },
    semibold: { fontWeight: 600 },
    bold: { fontWeight: 700 },
  };

  const textStyle = {
    ...styles.text[variant],
    ...sizeStyles[size],
    ...weightStyles[weight],
    margin: 0,
    ...style,
  };

  const Component = as as keyof JSX.IntrinsicElements;

  return (
    <Component className={className} style={textStyle}>
      {children}
    </Component>
  );
};

export default ThemeText;
