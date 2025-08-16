# Agent Spy - Frontend Dashboard Documentation

## Overview

The Agent Spy frontend is a modern React application that provides a comprehensive web-based dashboard for visualizing and exploring AI agent traces. Built with TypeScript, React 19, and Ant Design, it offers real-time monitoring, detailed trace inspection, and powerful filtering capabilities.

## Architecture

### Technology Stack
- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite for fast development and optimized builds
- **UI Library**: Ant Design (antd) for professional components
- **State Management**: TanStack React Query for server state
- **Styling**: Tailwind CSS for utility-first styling
- **Icons**: Ant Design Icons
- **Charts**: Recharts for statistics visualization
- **Timeline**: vis-timeline for advanced timeline visualization

### Project Structure
```
frontend/
├── src/
│   ├── App.tsx              # Main application component
│   ├── main.tsx             # Application entry point
│   ├── components/          # React components
│   │   ├── Dashboard.tsx    # Main dashboard layout
│   │   ├── TraceTable.tsx   # Root traces table
│   │   ├── TraceDetail.tsx  # Detailed trace view
│   │   ├── DashboardStats.tsx # Statistics cards
│   │   ├── SimpleTimeline.tsx # Basic timeline component
│   │   └── TraceTimeline.tsx  # Advanced timeline visualization
│   ├── hooks/               # Custom React hooks
│   │   └── useTraces.ts     # Data fetching hooks
│   ├── api/                 # API client
│   │   └── client.ts        # Axios configuration
│   ├── types/               # TypeScript definitions
│   │   └── traces.ts        # Type definitions for traces
│   ├── utils/               # Utility functions
│   │   └── formatters.ts    # Data formatting utilities
│   └── assets/              # Static assets
├── public/                  # Public assets
├── index.html              # HTML template
├── package.json            # Dependencies and scripts
├── vite.config.ts          # Vite configuration
├── tailwind.config.js      # Tailwind CSS configuration
├── tsconfig.json           # TypeScript configuration
└── nginx.conf              # Nginx configuration for Docker
```

## Core Components

### 1. Main Application (`App.tsx`)

The root component sets up the application context and providers:

```typescript
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ConfigProvider theme={theme}>
        <AntApp>
          <div className="min-h-screen bg-gray-50">
            <Dashboard />
          </div>
        </AntApp>
      </ConfigProvider>
    </QueryClientProvider>
  );
}
```

**Key Features:**
- **React Query Setup**: Configured with optimized defaults
- **Ant Design Theming**: Custom theme configuration
- **Global Error Boundary**: Comprehensive error handling

### 2. Dashboard Component (`Dashboard.tsx`)

The main dashboard component orchestrates the entire user interface:

```typescript
const Dashboard: React.FC = () => {
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null);
  const [isDetailExpanded, setIsDetailExpanded] = useState<boolean>(false);
  const [refreshTrigger, setRefreshTrigger] = useState<number>(0);

  // Health check to ensure backend is available
  const { isLoading: healthLoading, error: healthError } = useHealth();

  // Coordinated refresh for both root traces and trace detail
  const handleRefresh = useCallback(() => {
    setRefreshTrigger(prev => prev + 1);
  }, []);

  // ... component JSX
};
```

**Key Features:**
- **Master-Detail Layout**: Split view with trace table and detail panel
- **State Management**: Centralized state for selected traces and UI state
- **Health Monitoring**: Real-time backend connectivity status
- **Coordinated Refresh**: Synchronized updates across components
- **Responsive Design**: Adaptive layout for different screen sizes

### 3. Trace Table Component (`TraceTable.tsx`)

Displays root traces with advanced filtering and pagination:

```typescript
interface TraceTableProps {
  selectedTraceId: string | null;
  onTraceSelect: (traceId: string) => void;
  onRefresh: () => void;
  refreshTrigger: number;
  disabled?: boolean;
}
```

**Features:**
- **Real-time Data**: Auto-refreshing trace list
- **Advanced Filtering**: Filter by project, status, time range
- **Text Search**: Search across trace names and content
- **Pagination**: Efficient handling of large datasets
- **Selection State**: Visual indication of selected traces
- **Status Indicators**: Color-coded status badges
- **Duration Display**: Human-readable execution times

### 4. Trace Detail Component (`TraceDetail.tsx`)

Provides detailed hierarchical view of selected traces:

```typescript
interface TraceDetailProps {
  traceId: string;
  onClose: () => void;
  onToggleExpansion: () => void;
  isExpanded: boolean;
  refreshTrigger: number;
  disabled?: boolean;
}
```

**Features:**
- **Hierarchical Tree**: Expandable tree view of trace hierarchy
- **Rich Data Display**: Inputs, outputs, timing, and metadata
- **JSON Viewer**: Formatted JSON display for complex data
- **Timeline Integration**: Visual timeline of execution steps
- **Expandable Layout**: Full-screen mode for detailed analysis
- **Error Highlighting**: Clear error message display

### 5. Dashboard Statistics (`DashboardStats.tsx`)

Real-time statistics and metrics overview:

```typescript
const DashboardStats: React.FC = () => {
  const { data: summary, isLoading, error } = useDashboardSummary();

  // Calculate derived metrics
  const successRate = totalWithStatus > 0
    ? ((completedCount / totalWithStatus) * 100).toFixed(1)
    : '0';

  // ... render statistics cards
};
```

**Features:**
- **Key Metrics**: Total runs, traces, success rates
- **Status Distribution**: Breakdown by run status
- **Run Type Analysis**: Distribution by operation type
- **Project Overview**: Activity by project
- **Time-based Metrics**: Recent activity tracking
- **Visual Indicators**: Progress bars and trend indicators

## Data Flow Architecture

### State Management Strategy

The application uses a combination of local React state and React Query for optimal performance:

```typescript
// Local UI State (React useState)
- selectedTraceId: Currently selected trace
- isDetailExpanded: Detail panel expansion state
- refreshTrigger: Coordinated refresh mechanism

// Server State (React Query)
- Root traces data with caching
- Trace hierarchy data
- Dashboard statistics
- Health check status
```

### React Query Configuration

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 60000, // 1 minute
      refetchOnWindowFocus: false,
    },
  },
});
```

**Benefits:**
- **Automatic Caching**: Intelligent data caching and invalidation
- **Background Updates**: Automatic data refresh
- **Loading States**: Built-in loading and error states
- **Optimistic Updates**: Immediate UI feedback

### Custom Hooks (`useTraces.ts`)

Centralized data fetching logic with React Query:

```typescript
// Health check hook
export const useHealth = () => {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const response = await apiClient.get('/health');
      return response.data;
    },
    refetchInterval: 30000, // 30 seconds
    retry: 1,
  });
};

// Root traces hook with filtering
export const useRootTraces = (filters: TraceFilters, pagination: PaginationParams, refreshTrigger: number) => {
  return useQuery({
    queryKey: ['rootTraces', filters, pagination, refreshTrigger],
    queryFn: async () => {
      const params = { ...filters, ...pagination };
      const response = await apiClient.get('/api/v1/dashboard/runs/roots', { params });
      return response.data;
    },
    keepPreviousData: true,
  });
};

// Trace hierarchy hook
export const useTraceHierarchy = (traceId: string, refreshTrigger: number) => {
  return useQuery({
    queryKey: ['traceHierarchy', traceId, refreshTrigger],
    queryFn: async () => {
      const response = await apiClient.get(`/api/v1/dashboard/runs/${traceId}/hierarchy`);
      return response.data;
    },
    enabled: !!traceId,
  });
};

// Dashboard statistics hook
export const useDashboardSummary = () => {
  return useQuery({
    queryKey: ['dashboardSummary'],
    queryFn: async () => {
      const response = await apiClient.get('/api/v1/dashboard/stats/summary');
      return response.data;
    },
    refetchInterval: 30000, // 30 seconds
  });
};
```

## User Interface Design

### Layout System

The dashboard uses a flexible layout system based on CSS Grid and Flexbox:

```typescript
// Main layout structure
<Layout className="min-h-screen">
  <Header> {/* Navigation and status */} </Header>
  <Content>
    <DashboardStats /> {/* Statistics cards */}
    <div className="flex gap-6 overflow-hidden">
      {/* Master table */}
      <div className={selectedTraceId ? 'flex-1' : 'w-full'}>
        <TraceTable />
      </div>

      {/* Detail panel (conditional) */}
      {selectedTraceId && (
        <div className={isExpanded ? 'w-full' : 'w-120'}>
          <TraceDetail />
        </div>
      )}
    </div>
  </Content>
</Layout>
```

### Responsive Design

The interface adapts to different screen sizes:
- **Desktop**: Full master-detail layout
- **Tablet**: Collapsible detail panel
- **Mobile**: Stack layout with navigation

### Theme Configuration

Custom Ant Design theme for consistent branding:

```typescript
const theme = {
  token: {
    colorPrimary: '#1890ff',
    borderRadius: 6,
    fontSize: 14,
  },
  components: {
    Layout: {
      headerBg: '#ffffff',
      headerPadding: '0 24px',
    },
    Table: {
      headerBg: '#fafafa',
    },
  },
};
```

## Data Visualization

### Trace Table Features

Advanced table with rich functionality:

```typescript
// Column configuration
const columns = [
  {
    title: 'Status',
    dataIndex: 'status',
    render: (status: string) => <StatusBadge status={status} />,
    filters: statusFilters,
  },
  {
    title: 'Name',
    dataIndex: 'name',
    ellipsis: true,
    sorter: (a, b) => a.name.localeCompare(b.name),
  },
  {
    title: 'Type',
    dataIndex: 'run_type',
    filters: runTypeFilters,
  },
  {
    title: 'Duration',
    dataIndex: 'duration_ms',
    render: (duration: number) => formatDuration(duration),
    sorter: (a, b) => (a.duration_ms || 0) - (b.duration_ms || 0),
  },
  {
    title: 'Start Time',
    dataIndex: 'start_time',
    render: (time: string) => formatTimestamp(time),
    sorter: (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime(),
  },
];
```

### Hierarchical Tree Display

Interactive tree view for trace hierarchies:

```typescript
// Tree data transformation
const transformToTreeData = (node: RunHierarchyNode): DataNode => ({
  key: node.id,
  title: (
    <TraceNodeTitle
      node={node}
      onSelect={onNodeSelect}
    />
  ),
  children: node.children?.map(transformToTreeData),
  data: node,
});
```

### Timeline Visualization

Advanced timeline component using vis-timeline:

```typescript
// Timeline configuration
const options = {
  height: '400px',
  stack: true,
  showCurrentTime: false,
  zoomMin: 1000,
  zoomMax: 1000 * 60 * 60 * 24,
  format: {
    minorLabels: {
      millisecond: 'SSS',
      second: 's.SSS',
      minute: 'HH:mm:ss',
      hour: 'HH:mm',
    },
  },
};
```

## Performance Optimizations

### React Performance

```typescript
// Memoized components for expensive renders
const TraceTable = React.memo(({ selectedTraceId, onTraceSelect, ...props }) => {
  // Component implementation
});

// Optimized callbacks to prevent unnecessary re-renders
const handleTraceSelect = useCallback((traceId: string) => {
  setSelectedTraceId(traceId);
}, []);

// Debounced search to reduce API calls
const debouncedSearch = useMemo(
  () => debounce((value: string) => setSearchTerm(value), 300),
  []
);
```

### Data Loading Optimizations

```typescript
// Pagination for large datasets
const pagination = {
  current: currentPage,
  pageSize: 50,
  total: totalRuns,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total, range) =>
    `${range[0]}-${range[1]} of ${total} traces`,
};

// Optimistic updates for better UX
const handleRefresh = useCallback(() => {
  queryClient.invalidateQueries(['rootTraces']);
  queryClient.invalidateQueries(['traceHierarchy']);
}, [queryClient]);
```

### Bundle Optimization

Vite configuration for optimal builds:

```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          antd: ['antd'],
          charts: ['recharts'],
        },
      },
    },
  },
});
```

## Error Handling

### Error Boundaries

React error boundaries for graceful error handling:

```typescript
// Global error handling with React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        if (error.response?.status === 404) return false;
        return failureCount < 2;
      },
      onError: (error) => {
        console.error('Query error:', error);
        // Show user-friendly error message
      },
    },
  },
});
```

### User Feedback

Clear error states and loading indicators:

```typescript
// Loading states
if (isLoading) {
  return <Spin size="large" className="flex justify-center p-8" />;
}

// Error states
if (error) {
  return (
    <Alert
      message="Failed to load traces"
      description={error.message}
      type="error"
      showIcon
      action={
        <Button size="small" onClick={refetch}>
          Retry
        </Button>
      }
    />
  );
}
```

## Accessibility Features

### Keyboard Navigation
- **Tab Navigation**: Full keyboard accessibility
- **Arrow Keys**: Tree navigation support
- **Enter/Space**: Action triggers
- **Escape**: Modal/panel closing

### Screen Reader Support
- **ARIA Labels**: Comprehensive labeling
- **Role Attributes**: Proper semantic roles
- **Live Regions**: Dynamic content announcements
- **Focus Management**: Logical focus flow

### Visual Accessibility
- **Color Contrast**: WCAG AA compliance
- **Focus Indicators**: Clear focus states
- **Text Scaling**: Responsive text sizing
- **Motion Reduction**: Respect user preferences

## Development Workflow

### Local Development
```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Code Quality Tools
```bash
# Linting
npm run lint

# Type checking
npx tsc --noEmit

# Testing (planned)
npm run test
```

### Docker Development
```bash
# Development with hot reloading
docker compose -f docker/docker-compose.dev.yml up -d

# Access logs
docker compose -f docker/docker-compose.dev.yml logs -f frontend
```

## Configuration

### Environment Variables
```bash
# API endpoint configuration
VITE_API_BASE_URL=http://localhost:8000

# Feature flags (planned)
VITE_ENABLE_TIMELINE=true
VITE_ENABLE_CHARTS=true
```

### Build Configuration
- **TypeScript**: Strict type checking enabled
- **ESLint**: Code quality and consistency
- **Tailwind**: Utility-first CSS framework
- **PostCSS**: CSS processing and optimization

## Future Enhancements

### Planned Features
- **Advanced Filtering**: More sophisticated filter options
- **Export Functionality**: CSV/JSON export of trace data
- **Real-time Updates**: WebSocket integration for live updates
- **Custom Dashboards**: User-configurable dashboard layouts
- **Trace Comparison**: Side-by-side trace comparison
- **Performance Analytics**: Advanced performance insights

### Technical Improvements
- **Testing Suite**: Comprehensive unit and integration tests
- **Storybook**: Component documentation and testing
- **PWA Support**: Offline functionality and app-like experience
- **Internationalization**: Multi-language support
- **Theme Customization**: User-configurable themes
