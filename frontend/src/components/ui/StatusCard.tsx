import React from "react";
import { useThemeColors, useThemeSpacing } from "../../hooks/useThemeStyles";
import Card from "./Card";
import { ThemeIcon, ThemeText } from "./theme";

interface StatusItem {
  icon: React.ReactNode;
  title: string;
  count: number;
  iconColor?:
    | "primary"
    | "secondary"
    | "success"
    | "warning"
    | "error"
    | "info"
    | "muted"
    | "inverse";
}

interface StatusCardProps {
  title: string;
  description: string;
  headerIcon: React.ReactNode;
  headerIconColor?:
    | "primary"
    | "secondary"
    | "success"
    | "warning"
    | "error"
    | "info"
    | "muted"
    | "inverse";
  items: StatusItem[];
  className?: string;
}

const StatusCard: React.FC<StatusCardProps> = ({
  title,
  description,
  headerIcon,
  headerIconColor = "primary",
  items,
  className = "",
}) => {
  const { getColor } = useThemeColors();
  const { getSpacing } = useThemeSpacing();

  return (
    <Card className={className}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center" style={{ gap: getSpacing("6") }}>
          <div
            className="flex items-center justify-center w-10 h-10 rounded-xl"
            style={{
              backgroundColor: getColor("surface-hover"),
            }}
          >
            <ThemeIcon size="lg" color={headerIconColor}>
              {headerIcon}
            </ThemeIcon>
          </div>
          <div style={{ padding: "4px 0" }}>
            <ThemeText
              size="xl"
              weight="semibold"
              variant="primary"
              as="h4"
              style={{ margin: 0, padding: 0, lineHeight: 1.2 }}
            >
              {title}
            </ThemeText>
            <ThemeText
              variant="secondary"
              size="base"
              weight="normal"
              as="p"
              style={{ margin: 0, padding: 0, lineHeight: 1.2 }}
            >
              {description}
            </ThemeText>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {items.map((item, index) => (
          <div
            key={index}
            className="flex justify-between items-center p-4 rounded-lg"
            style={{
              backgroundColor: getColor("surface-hover"),
              borderColor: getColor("border"),
              gap: getSpacing("3"),
            }}
          >
            <span
              className="flex items-center"
              style={{
                gap: getSpacing("3"),
                color: getColor("text"),
              }}
            >
              <div
                className="flex items-center justify-center w-8 h-8 rounded-lg"
                style={{
                  backgroundColor: getColor("surface-active"),
                }}
              >
                <ThemeIcon size="sm" color={item.iconColor || "text-secondary"}>
                  {item.icon}
                </ThemeIcon>
              </div>
              <ThemeText variant="primary" size="base" weight="medium">
                {item.title}
              </ThemeText>
            </span>
            <ThemeText variant="primary" size="lg" weight="bold">
              {item.count}
            </ThemeText>
          </div>
        ))}
      </div>
    </Card>
  );
};

export default StatusCard;
