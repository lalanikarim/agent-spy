import { Typography } from "antd";
import React from "react";
import Card from "./Card";

const { Title, Text } = Typography;

interface StatusItem {
  icon: React.ReactNode;
  title: string;
  count: number;
  iconBgColor?: string;
  iconColor?: string;
}

interface StatusCardProps {
  title: string;
  description: string;
  headerIcon: React.ReactNode;
  headerIconBgColor?: string;
  headerIconColor?: string;
  items: StatusItem[];
  className?: string;
}

const StatusCard: React.FC<StatusCardProps> = ({
  title,
  description,
  headerIcon,
  headerIconBgColor = "bg-blue-100",
  headerIconColor = "text-blue-600",
  items,
  className = "",
}) => {
  return (
    <Card className={className}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center" style={{ gap: "24px" }}>
          <div
            className={`flex items-center justify-center w-10 h-10 ${headerIconBgColor} rounded-xl`}
          >
            <div className={`text-xl ${headerIconColor}`}>{headerIcon}</div>
          </div>
          <div style={{ padding: "4px 0" }}>
            <Title
              level={4}
              className="m-0 p-0 text-gray-900 dark:text-gray-100"
              style={{ margin: 0, padding: 0, lineHeight: 1.2 }}
            >
              {title}
            </Title>
            <Text
              className="text-gray-600 dark:text-gray-400 m-0 p-0"
              style={{ margin: 0, padding: 0, lineHeight: 1.2 }}
            >
              {description}
            </Text>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        {items.map((item, index) => (
          <div
            key={index}
            className="flex justify-between items-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg"
            style={{
              backgroundColor: "var(--color-surface-hover)",
              borderColor: "var(--color-border)",
            }}
          >
            <span
              className="flex items-center text-gray-800 dark:text-gray-200"
              style={{
                gap: "12px",
                color: "var(--color-text)",
              }}
            >
              <div
                className={`flex items-center justify-center w-8 h-8 ${
                  item.iconBgColor || "bg-gray-100 dark:bg-gray-600"
                } rounded-lg`}
              >
                <div
                  className={
                    item.iconColor || "text-gray-600 dark:text-gray-300"
                  }
                  style={{
                    color: item.iconColor
                      ? undefined
                      : "var(--color-text-secondary)",
                  }}
                >
                  {item.icon}
                </div>
              </div>
              <span
                className="font-medium"
                style={{ color: "var(--color-text)" }}
              >
                {item.title}
              </span>
            </span>
            <span
              className="font-bold text-lg text-gray-900 dark:text-gray-100"
              style={{ color: "var(--color-text)" }}
            >
              {item.count}
            </span>
          </div>
        ))}
      </div>
    </Card>
  );
};

export default StatusCard;
