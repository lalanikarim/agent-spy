import React from "react";

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
  hover = true,
  style = {},
}) => {
  const paddingValues = {
    sm: "8px",
    md: "12px",
    lg: "16px",
    xl: "20px",
  };

  const baseClasses = "border";
  const hoverClasses = hover
    ? "hover:shadow-2xl hover:border-gray-300 dark:hover:border-gray-600 transition-all duration-200"
    : "";

  return (
    <div
      className={`${baseClasses} ${hoverClasses} ${className}`}
      style={{
        backgroundColor: "var(--color-surface)",
        borderColor: "var(--color-border)",
        borderRadius: "16px",
        padding: paddingValues[padding],
        boxShadow: "0 25px 50px -12px rgb(0 0 0 / 0.25)",
        ...style,
      }}
    >
      {children}
    </div>
  );
};

export default Card;
