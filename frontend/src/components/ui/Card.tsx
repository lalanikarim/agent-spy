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

  const baseClasses = "bg-white";
  const hoverClasses = hover
    ? "hover:shadow-xl hover:border-gray-200 transition-all duration-200"
    : "";

  return (
    <div
      className={`${baseClasses} ${hoverClasses} ${className}`}
      style={{
        backgroundColor: "white",
        borderRadius: "16px",
        padding: paddingValues[padding],
        boxShadow:
          "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
        ...style,
      }}
    >
      {children}
    </div>
  );
};

export default Card;
