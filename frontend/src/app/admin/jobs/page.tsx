"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { queryKeys } from "@/lib/query-keys";
import { getAdminJobs } from "@/lib/api";
import { formatDateTime } from "@/lib/formatters";
import { Cpu, RefreshCw, CheckCircle2, XCircle, Clock } from "lucide-react";

export default function AdminJobsPage() {
  const [statusFilter, setStatusFilter] = useState<string>("");

  const {
    data: jobs,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: queryKeys.adminJobs({ status: statusFilter }),
    queryFn: () => getAdminJobs({ status: statusFilter || undefined }),
    // Poll every 2000ms if any job is queued or running
    refetchInterval: (query) => {
      const data = query.state.data;
      const hasActive = data?.some((j) => ["queued", "running"].includes(j.status));
      return hasActive ? 2000 : false;
    },
  });

  const activeJobCount = jobs?.filter((j) => ["queued", "running"].includes(j.status)).length ?? 0;

  return (
    <AppShell>
      <PageHeader
        title="Background Ingestion Jobs"
        subtitle="Asynchronous PDF chunking, embedding generation, and Qdrant vector indexing worker tasks."
        action={
          <div className="flex items-center gap-3">
            {activeJobCount > 0 && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#FFF4E5] text-status-warningText border border-[#F6D09F] animate-pulse">
                <Clock className="w-3.5 h-3.5" />
                {activeJobCount} Active Task(s) Polling
              </span>
            )}
            <button
              onClick={() => refetch()}
              className="p-2 rounded-lg border border-washi-border hover:bg-surface-muted transition-colors text-ink-muted hover:text-ink"
              title="Refresh Jobs"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        }
      />

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 mb-6 border-b border-washi-border pb-3 text-xs">
        {["", "queued", "running", "succeeded", "failed"].map((st) => (
          <button
            key={st}
            onClick={() => setStatusFilter(st)}
            className={`px-3 py-1.5 rounded-lg capitalize font-medium transition-colors ${
              statusFilter === st
                ? "bg-aoi text-white shadow-xs"
                : "bg-surface text-ink-muted hover:text-ink hover:bg-surface-muted border border-washi-border"
            }`}
          >
            {st || "All Jobs"}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          <div className="h-16 skeleton washi-panel" />
          <div className="h-16 skeleton washi-panel" />
          <div className="h-16 skeleton washi-panel" />
        </div>
      ) : error ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : !jobs || !Array.isArray(jobs) || jobs.length === 0 ? (
        <EmptyState
          title="No Ingestion Jobs"
          description="There are currently no background document indexing jobs recorded."
        />
      ) : (
        <div className="washi-panel overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-washi-border bg-surface-muted text-ink-muted uppercase tracking-wider font-semibold">
                  <th className="py-3 px-4">Job Reference</th>
                  <th className="py-3 px-4">Document Version</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Attempts</th>
                  <th className="py-3 px-4">Created Timestamp</th>
                  <th className="py-3 px-4">Completed Timestamp</th>
                  <th className="py-3 px-4">Result / Diagnostics</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-washi-border/60">
                {jobs.map((job) => (
                  <tr key={job.public_id} className="hover:bg-surface-muted/50 transition-colors">
                    <td className="py-3.5 px-4 font-mono font-medium text-ink">
                      {job.public_id}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-ink-muted">
                      Ver #{job.document_version_id}
                    </td>
                    <td className="py-3.5 px-4">
                      <StatusBadge status={job.status} />
                    </td>
                    <td className="py-3.5 px-4 font-mono text-ink">
                      {job.attempts}
                    </td>
                    <td className="py-3.5 px-4 text-ink-muted">
                      {formatDateTime(job.created_at)}
                    </td>
                    <td className="py-3.5 px-4 text-ink-muted">
                      {job.finished_at ? formatDateTime(job.finished_at) : "In progress..."}
                    </td>
                    <td className="py-3.5 px-4">
                      {job.error_message ? (
                        <span className="text-status-dangerText font-mono text-[11px] block max-w-xs truncate" title={job.error_message}>
                          {job.error_message}
                        </span>
                      ) : job.result ? (
                        <span className="text-ink-muted font-mono text-[11px] block max-w-xs truncate">
                          {JSON.stringify(job.result)}
                        </span>
                      ) : (
                        <span className="text-ink-muted italic">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </AppShell>
  );
}
