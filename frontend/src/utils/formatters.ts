import dayjs from "dayjs";
import duration from "dayjs/plugin/duration";
import relativeTime from "dayjs/plugin/relativeTime";
import timezone from "dayjs/plugin/timezone";
import utc from "dayjs/plugin/utc";

// Extend dayjs with plugins
dayjs.extend(relativeTime);
dayjs.extend(duration);
dayjs.extend(utc);
dayjs.extend(timezone);

// Get user's timezone (default to UTC if not available)
const getUserTimezone = (): string => {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
  } catch {
    return "UTC";
  }
};

// Convert UTC date string to user's local timezone
const convertToLocalTime = (
  dateString: string | null | undefined
): dayjs.Dayjs | null => {
  if (!dateString) return null;

  try {
    // Parse the date string (should be UTC from backend)
    const utcDate = dayjs.utc(dateString);
    if (!utcDate.isValid()) {
      console.warn("Invalid date string:", dateString);
      return null;
    }

    // Convert to user's local timezone
    return utcDate.tz(getUserTimezone());
  } catch (error) {
    console.error("Error converting date to local timezone:", error);
    return null;
  }
};

// Format date/time utilities
export const formatters = {
  // Format absolute time with timezone
  formatDateTime: (dateString: string | null | undefined): string => {
    if (!dateString) return "N/A";
    const localDate = convertToLocalTime(dateString);
    if (!localDate) return "N/A";
    return localDate.format("YYYY-MM-DD HH:mm:ss z");
  },

  // Format relative time (e.g., "2 minutes ago")
  formatRelativeTime: (dateString: string | null | undefined): string => {
    if (!dateString) return "N/A";
    const localDate = convertToLocalTime(dateString);
    if (!localDate) return "N/A";
    return localDate.fromNow();
  },

  // Format date only (without time)
  formatDate: (dateString: string | null | undefined): string => {
    if (!dateString) return "N/A";
    const localDate = convertToLocalTime(dateString);
    if (!localDate) return "N/A";
    return localDate.format("YYYY-MM-DD");
  },

  // Format time only (without date)
  formatTime: (dateString: string | null | undefined): string => {
    if (!dateString) return "N/A";
    const localDate = convertToLocalTime(dateString);
    if (!localDate) return "N/A";
    return localDate.format("HH:mm:ss z");
  },

  // Get user's current timezone
  getUserTimezone: (): string => {
    return getUserTimezone();
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
    // Ensure both times are in UTC for accurate calculation
    const start = dayjs.utc(startTime);
    const end = dayjs.utc(endTime);
    return end.diff(start);
  },

  // Calculate elapsed time for running tasks (from start time to now)
  calculateElapsedTime: (startTime: string | null): number | null => {
    if (!startTime) return null;
    // Ensure both times are in UTC for accurate calculation
    const start = dayjs.utc(startTime);
    const now = dayjs.utc();
    return now.diff(start);
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
  formatJSON: (obj: unknown): string => {
    if (!obj) return "N/A";
    try {
      return JSON.stringify(obj, null, 2);
    } catch {
      return "Invalid JSON";
    }
  },
};
