import React from "react";
import { ThemeCard } from "./theme";

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: "sm" | "md" | "lg" | "xl";
  hover?: boolean;
  style?: React.CSSProperties;
}

const Card: React.FC<CardProps> = ({
  children,
  className = "",
  padding = "lg",
  hover = false, // Changed default to false to match original behavior
  style = {},
}) => {
  // Map old padding values to new theme padding values
  const paddingMap = {
    sm: "small" as const,
    md: "medium" as const,
    lg: "medium" as const,
    xl: "large" as const,
  };

  return (
    <ThemeCard
      variant={hover ? "interactive" : "default"}
      padding={paddingMap[padding]}
      hover={hover}
      className={className}
      style={style}
    >
      {children}
    </ThemeCard>
  );
};

export default Card;
