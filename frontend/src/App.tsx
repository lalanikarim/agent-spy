import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider, App as AntApp } from 'antd';
import Dashboard from './components/Dashboard';
import './App.css';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 60000, // 1 minute
      refetchOnWindowFocus: false,
    },
  },
});

// Ant Design theme configuration
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

export default App;