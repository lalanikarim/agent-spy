import React from "react";
import { useThemeColors, useThemeSpacing } from "../../hooks/useThemeStyles";
import Card from "./Card";
import { ThemeIcon, ThemeText } from "./theme";

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  iconColor?:
    | "primary"
    | "secondary"
    | "success"
    | "warning"
    | "error"
    | "info"
    | "muted"
    | "inverse";
  className?: string;
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  icon,
  iconColor = "primary",
  className = "",
}) => {
  const { getColor } = useThemeColors();
  const { getSpacing } = useThemeSpacing();

  return (
    <Card className={`h-full ${className}`}>
      {/* First row: Title */}
      <ThemeText
        variant="secondary"
        size="sm"
        weight="medium"
        style={{ marginBottom: getSpacing("4") }}
      >
        {title}
      </ThemeText>

      {/* Second row: Icon, value, and description */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div
            className="flex items-center justify-center w-14 h-14 rounded-lg transition-colors duration-200 flex-shrink-0"
            style={{
              backgroundColor: getColor("surface-hover"),
              gap: getSpacing("4"),
            }}
          >
            <ThemeIcon size="xl" color={iconColor}>
              {icon}
            </ThemeIcon>
          </div>
          <div className="flex flex-col">
            <ThemeText size="3xl" weight="bold" variant="primary">
              {value}
            </ThemeText>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default StatCard;
