import React from "react";
import Card from "./Card";

interface StatCardProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  iconBgColor?: string;
  iconColor?: string;
  className?: string;
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  icon,
  iconBgColor = "bg-blue-100",
  iconColor = "text-blue-600",
  className = "",
}) => {
  return (
    <Card className={`h-full ${className}`}>
      {/* First row: Title */}
      <div className="text-gray-400 dark:text-gray-500 text-sm font-medium mb-4" style={{ color: "var(--color-text-secondary)" }}>{title}</div>

      {/* Second row: Icon, value, and description */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div
            className={`flex items-center justify-center w-14 h-14 ${iconBgColor} rounded-lg transition-colors duration-200 flex-shrink-0`}
          >
            <div className={`text-2xl ${iconColor}`}>{icon}</div>
          </div>
          <div className="flex flex-col">
            <div className={`text-4xl font-bold ${iconColor}`}>{value}</div>
          </div>
        </div>
      </div>
    </Card>
  );
};

export default StatCard;
