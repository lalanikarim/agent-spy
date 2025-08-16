import dayjs from "dayjs";
import duration from "dayjs/plugin/duration";
import relativeTime from "dayjs/plugin/relativeTime";

// Extend dayjs with plugins
dayjs.extend(relativeTime);
dayjs.extend(duration);

// Format date/time utilities
export const formatters = {
  // Format absolute time
  formatDateTime: (dateString: string | null | undefined): string => {
    if (!dateString) return "N/A";
    return dayjs(dateString).format("YYYY-MM-DD HH:mm:ss");
  },

  // Format relative time (e.g., "2 minutes ago")
  formatRelativeTime: (dateString: string | null | undefined): string => {
    if (!dateString) return "N/A";
    return dayjs(dateString).fromNow();
  },

  // Format duration in milliseconds to human readable
  formatDuration: (durationMs: number | null | undefined): string => {
    if (!durationMs) return "N/A";

    if (durationMs < 1000) {
      return `${durationMs}ms`;
    }

    const seconds = Math.floor(durationMs / 1000);
    if (seconds < 60) {
      return `${seconds}s`;
    }

    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    if (minutes < 60) {
      return remainingSeconds > 0
        ? `${minutes}m ${remainingSeconds}s`
        : `${minutes}m`;
    }

    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return remainingMinutes > 0
      ? `${hours}h ${remainingMinutes}m`
      : `${hours}h`;
  },

  // Calculate duration between start and end times
  calculateDuration: (
    startTime: string | null,
    endTime: string | null
  ): number | null => {
    if (!startTime || !endTime) return null;
    return dayjs(endTime).diff(dayjs(startTime));
  },

  // Calculate elapsed time for running tasks (from start time to now)
  calculateElapsedTime: (startTime: string | null): number | null => {
    if (!startTime) return null;
    return dayjs().diff(dayjs(startTime));
  },

  // Format duration for tasks, showing elapsed time for running tasks
  formatTaskDuration: (
    durationMs: number | null | undefined,
    startTime: string | null,
    endTime: string | null,
    status: string
  ): string => {
    // For completed/failed tasks, use the actual duration
    if (
      durationMs &&
      (status.toLowerCase() === "completed" ||
        status.toLowerCase() === "failed")
    ) {
      return formatters.formatDuration(durationMs);
    }

    // For running tasks, calculate elapsed time
    if (status.toLowerCase() === "running" && startTime) {
      const elapsedMs = formatters.calculateElapsedTime(startTime);
      return elapsedMs ? formatters.formatDuration(elapsedMs) : "N/A";
    }

    // Fallback to calculated duration or N/A
    const calculatedDuration =
      durationMs || formatters.calculateDuration(startTime, endTime);
    return formatters.formatDuration(calculatedDuration);
  },

  // Format status with appropriate styling
  formatStatus: (status: string): { text: string; color: string } => {
    switch (status.toLowerCase()) {
      case "completed":
        return { text: "Completed", color: "green" };
      case "running":
        return { text: "Running", color: "blue" };
      case "failed":
        return { text: "Failed", color: "red" };
      default:
        return { text: status, color: "default" };
    }
  },

  // Format run type with appropriate icon
  formatRunType: (runType: string): { text: string; icon: string } => {
    switch (runType.toLowerCase()) {
      case "chain":
        return { text: "Chain", icon: "🔗" };
      case "llm":
        return { text: "LLM", icon: "🤖" };
      case "tool":
        return { text: "Tool", icon: "🔧" };
      case "retrieval":
        return { text: "Retrieval", icon: "📚" };
      default:
        return { text: runType, icon: "📋" };
    }
  },

  // Format large numbers (e.g., 1000 -> 1K)
  formatNumber: (num: number): string => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`;
    }
    if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`;
    }
    return num.toString();
  },

  // Truncate long strings
  truncateString: (str: string, maxLength: number = 50): string => {
    if (str.length <= maxLength) return str;
    return `${str.substring(0, maxLength)}...`;
  },

  // Format JSON for display
  formatJSON: (obj: any): string => {
    if (!obj) return "N/A";
    try {
      return JSON.stringify(obj, null, 2);
    } catch {
      return "Invalid JSON";
    }
  },
};
