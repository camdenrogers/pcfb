"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { RefreshCw, BrainCircuit } from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type JobStatus = {
  status: "idle" | "running" | "success" | "error";
  last_run: string | null;
  message: string | null;
};

type Status = {
  refresh: JobStatus;
  retrain: JobStatus;
};

function StatusBadge({ status }: { status: JobStatus["status"] }) {
  const variants: Record<string, string> = {
    idle: "secondary",
    running: "outline",
    success: "default",
    error: "destructive",
  };
  return <Badge variant={variants[status] as any}>{status}</Badge>;
}

function RunLog({ entries }: { entries: string[] }) {
  return (
    <div className="rounded-md bg-black p-4 font-mono text-xs text-green-400 h-48 overflow-y-auto">
      {entries.length === 0 ? (
        <span className="text-zinc-500">No activity yet...</span>
      ) : (
        entries.map((e, i) => <div key={i}>{e}</div>)
      )}
    </div>
  );
}

function formatTime(isoString: string) {
  return new Date(isoString).toLocaleString("en-US", {
    timeZone: "America/New_York",
    dateStyle: "short",
    timeStyle: "medium",
  });
}

export default function ControlPage() {
  const [status, setStatus] = useState<Status | null>(null);
  const [log, setLog] = useState<string[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [retraining, setRetraining] = useState(false);
  const prevStatus = useRef<Status | null>(null);

  const addLog = (msg: string) =>
    setLog((prev) => [
      `[${new Date().toLocaleTimeString("en-US", { timeZone: "America/New_York" })}] ${msg}`,
      ...prev,
    ]);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/status`);
      const data: Status = await res.json();
      const prev = prevStatus.current;

      if (prev) {
        if (prev.refresh.status !== data.refresh.status) {
          if (data.refresh.status === "success")
            addLog(`✓ Refresh: ${data.refresh.message}`);
          if (data.refresh.status === "error")
            addLog(`✗ Refresh error: ${data.refresh.message}`);
          if (data.refresh.status === "running") addLog("Refresh running...");
        }
        if (prev.retrain.status !== data.retrain.status) {
          if (data.retrain.status === "success")
            addLog(`✓ Retrain: ${data.retrain.message}`);
          if (data.retrain.status === "error")
            addLog(`✗ Retrain error: ${data.retrain.message}`);
          if (data.retrain.status === "running") addLog("Retrain running...");
        }
      }

      prevStatus.current = data; // ← update AFTER transition check
      setStatus(data);
    } catch {
      addLog("ERROR: Could not reach API");
    }
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  async function handleRefresh() {
    setRefreshing(true);
    addLog("Starting data refresh...");
    try {
      await fetch(`${API_BASE}/api/refresh`, { method: "POST" });
    } catch {
      addLog("ERROR: Failed to start refresh");
    } finally {
      setRefreshing(false);
    }
  }

  async function handleRetrain() {
    setRetraining(true);
    addLog("Starting model retrain...");
    try {
      await fetch(`${API_BASE}/api/retrain`, { method: "POST" });
    } catch {
      addLog("ERROR: Failed to start retrain");
    } finally {
      setRetraining(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Control Center</h1>
        <p className="text-muted-foreground text-sm mt-1">
          Manage data ingestion and model training
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Refresh Data</CardTitle>
              {status && <StatusBadge status={status.refresh.status} />}
            </div>
            <CardDescription>
              Pull latest scores, stats, and schedules from CFBD
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {status?.refresh.last_run && (
              <p className="text-xs text-muted-foreground">
                Last run: {formatTime(status.refresh.last_run)}
              </p>
            )}
            <Button
              onClick={handleRefresh}
              disabled={refreshing || status?.refresh.status === "running"}
              className="w-full"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              {status?.refresh.status === "running"
                ? "Refreshing..."
                : "Refresh Data"}
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Retrain Model</CardTitle>
              {status && <StatusBadge status={status.retrain.status} />}
            </div>
            <CardDescription>
              Retrain the spread prediction model on latest data
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {status?.retrain.last_run && (
              <p className="text-xs text-muted-foreground">
                Last run: {formatTime(status.retrain.last_run)}
              </p>
            )}
            <Button
              onClick={handleRetrain}
              disabled={retraining || status?.retrain.status === "running"}
              variant="outline"
              className="w-full"
            >
              <BrainCircuit className="mr-2 h-4 w-4" />
              {status?.retrain.status === "running"
                ? "Retraining..."
                : "Retrain Model"}
            </Button>
            <p className="text-xs text-muted-foreground">
              This may take a few minutes
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="flex flex-col gap-2">
        <h2 className="text-sm font-medium">Run Log</h2>
        <RunLog entries={log} />
      </div>
    </div>
  );
}
