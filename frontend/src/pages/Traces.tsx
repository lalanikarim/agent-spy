import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import AppLayout from "../components/AppLayout";
import TraceDetail from "../components/TraceDetail";
import TraceTable from "../components/TraceTable";
import Card from "../components/ui/Card";
import { useHealth, useTraceHierarchy } from "../hooks/useTraces";

const Traces: React.FC = () => {
  const { error: healthError } = useHealth();

  const params = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const selectedTraceId = useMemo(
    () => params.traceId ?? null,
    [params.traceId]
  );
  const isDetailExpanded = useMemo(
    () => searchParams.get("expanded") === "1",
    [searchParams]
  );

  const [refreshTrigger, setRefreshTrigger] = useState<number>(0);

  const { isLoading: hierarchyLoading } = useTraceHierarchy(selectedTraceId, {
    enabled: !healthError && !!selectedTraceId,
  });

  // Set document title
  useEffect(() => {
    if (selectedTraceId) {
      document.title = `Traces | ${selectedTraceId}`;
    } else {
      document.title = "Traces | Agent Spy";
    }
  }, [selectedTraceId]);

  const handleRefresh = useCallback(() => {
    setRefreshTrigger((prev) => prev + 1);
  }, []);

  const handleTraceSelect = useCallback(
    (traceId: string) => {
      // Preserve current filters/search/pagination params
      const next = new URLSearchParams(searchParams);
      navigate({ pathname: `/traces/${traceId}`, search: next.toString() });
    },
    [navigate, searchParams]
  );

  const handleTraceDeselect = useCallback(() => {
    // Preserve current filters/search/pagination params but clear trace
    const next = new URLSearchParams(searchParams);
    navigate({ pathname: "/traces", search: next.toString() });
  }, [navigate, searchParams]);

  const handleToggleExpansion = useCallback(() => {
    const next = new URLSearchParams(searchParams);
    if (isDetailExpanded) {
      next.delete("expanded");
    } else {
      next.set("expanded", "1");
    }
    setSearchParams(next, { replace: true });
  }, [isDetailExpanded, searchParams, setSearchParams]);

  return (
    <AppLayout>
      <div className="flex gap-8">
        {/* Master Table - Root Traces */}
        {!isDetailExpanded && (
          <div className={selectedTraceId ? "flex-1 min-w-0" : "w-full"}>
            <Card className="h-full shadow-2xl">
              <TraceTable
                selectedTraceId={selectedTraceId}
                onTraceSelect={handleTraceSelect}
                onRefresh={handleRefresh}
                refreshTrigger={refreshTrigger}
                disabled={!!healthError}
              />
            </Card>
          </div>
        )}

        {/* Detail View - Trace Hierarchy (only show when trace selected) */}
        {selectedTraceId && (
          <div
            className={isDetailExpanded ? "w-full" : "w-120 flex-shrink-0"}
            style={
              !isDetailExpanded
                ? { width: "480px", minWidth: "480px", maxWidth: "480px" }
                : {}
            }
          >
            <TraceDetail
              traceId={selectedTraceId}
              onClose={handleTraceDeselect}
              onToggleExpansion={handleToggleExpansion}
              isExpanded={isDetailExpanded}
              refreshTrigger={refreshTrigger}
              onRefresh={handleRefresh}
              refreshLoading={hierarchyLoading}
              disabled={!!healthError}
            />
          </div>
        )}
      </div>
    </AppLayout>
  );
};

export default Traces;
