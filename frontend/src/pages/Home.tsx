import React, { useEffect } from "react";
import AppLayout from "../components/AppLayout";
import DashboardStats from "../components/DashboardStats";

const Home: React.FC = () => {
  useEffect(() => {
    document.title = "Home | Agent Spy";
  }, []);

  return (
    <AppLayout>
      <div className="mb-8">
        <DashboardStats />
      </div>
    </AppLayout>
  );
};

export default Home;
