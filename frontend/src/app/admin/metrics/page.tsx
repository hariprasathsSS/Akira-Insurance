"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { ErrorState } from "@/components/ui/ErrorState";
import { queryKeys } from "@/lib/query-keys";
import { getAdminMetrics } from "@/lib/api";
import { formatINR } from "@/lib/formatters";
import {
  BarChart3,
  Zap,
  DollarSign,
  ShieldCheck,
  Layers,
  Cpu,
  CheckCircle2,
  ExternalLink,
} from "lucide-react";

export default function AdminMetricsPage() {
  const { data: metrics, isLoading, error, refetch } = useQuery({
    queryKey: queryKeys.adminMetrics,
    queryFn: getAdminMetrics,
  });

  const stpRate = metrics?.stp_rate_percent ?? 0;

  return (
    <AppShell>
      <PageHeader
        title="Operations & Portfolio Metrics"
        subtitle="Aggregate claims volume, STP throughput ratios, average settlement values, and policy counts."
        action={
          metrics?.langfuse_dashboard_url && (
            <a
              href={metrics.langfuse_dashboard_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-aoi-wash text-aoi hover:text-aoi-deep border border-aoi/30 transition-colors"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              Langfuse Traces Dashboard
            </a>
          )
        }
      />

      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="h-36 skeleton washi-panel" />
          <div className="h-36 skeleton washi-panel" />
          <div className="h-36 skeleton washi-panel" />
          <div className="h-36 skeleton washi-panel" />
        </div>
      ) : error ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : !metrics ? null : (
        <div className="space-y-8">
          {/* Top KPI Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Total Claims */}
            <div className="washi-panel p-6 flex flex-col justify-between">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-semibold uppercase tracking-wider text-ink-muted">
                  Claims Volume
                </span>
                <div className="w-8 h-8 rounded-lg bg-aoi-wash text-aoi flex items-center justify-center">
                  <BarChart3 className="w-4 h-4" />
                </div>
              </div>
              <div>
                <div className="text-3xl font-serif font-bold text-ink">
                  {metrics.total_claims ?? 0}
                </div>
                <div className="flex items-center gap-2 mt-1 text-xs text-ink-muted">
                  <span className="text-status-warningText font-semibold">
                    {metrics.open_claims ?? 0} open
                  </span>
                  <span>•</span>
                  <span>{metrics.pending_review_count ?? 0} pending</span>
                </div>
              </div>
            </div>

            {/* STP Rate & Count */}
            <div className="washi-panel p-6 flex flex-col justify-between">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-semibold uppercase tracking-wider text-ink-muted">
                  Straight-Through (STP)
                </span>
                <div className="w-8 h-8 rounded-lg bg-matcha-soft text-status-successText flex items-center justify-center">
                  <Zap className="w-4 h-4" />
                </div>
              </div>
              <div>
                <div className="text-3xl font-serif font-bold text-ink">
                  {stpRate.toFixed(1)}%
                </div>
                <p className="text-xs text-ink-muted mt-1">
                  {metrics.stp_count ?? 0} automated payouts under threshold
                </p>
              </div>
            </div>

            {/* In-Force Policies */}
            <div className="washi-panel p-6 flex flex-col justify-between">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-semibold uppercase tracking-wider text-ink-muted">
                  Active In-Force Policies
                </span>
                <div className="w-8 h-8 rounded-lg bg-surface-muted text-ink flex items-center justify-center">
                  <ShieldCheck className="w-4 h-4" />
                </div>
              </div>
              <div>
                <div className="text-3xl font-serif font-bold text-ink">
                  {metrics.active_policies ?? 0}
                </div>
                <p className="text-xs text-ink-muted mt-1">
                  Insured customer subscriptions
                </p>
              </div>
            </div>

            {/* Document Families & Active Versions */}
            <div className="washi-panel p-6 flex flex-col justify-between">
              <div className="flex items-center justify-between mb-4">
                <span className="text-xs font-semibold uppercase tracking-wider text-ink-muted">
                  Policy Documents
                </span>
                <div className="w-8 h-8 rounded-lg bg-sakura-soft text-ink-muted flex items-center justify-center">
                  <Layers className="w-4 h-4" />
                </div>
              </div>
              <div>
                <div className="text-3xl font-serif font-bold text-ink">
                  {metrics.document_families_count ?? 0}
                </div>
                <p className="text-xs text-ink-muted mt-1">
                  {metrics.active_versions_count ?? 0} active indexed version(s)
                </p>
              </div>
            </div>
          </div>

          {/* Operational Distribution Panel */}
          <div className="washi-panel p-6 sm:p-8">
            <h3 className="font-serif font-bold text-lg text-ink mb-2">
              Operational Automation Ratio
            </h3>
            <p className="text-xs text-ink-muted mb-6">
              Evaluation of straight-through automatic settlements versus human adjuster review assignments.
            </p>

            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <span className="font-semibold text-ink flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-status-successText" />
                    Automated STP Settlement Ratio
                  </span>
                  <span className="font-mono font-bold text-status-successText">
                    {stpRate.toFixed(1)}%
                  </span>
                </div>
                <div className="h-3 w-full bg-surface-muted rounded-full overflow-hidden border border-washi-border">
                  <div
                    className="h-full bg-matcha transition-all duration-500 rounded-full"
                    style={{ width: `${Math.min(100, Math.max(0, stpRate))}%` }}
                  />
                </div>
              </div>

              <div className="pt-4 border-t border-washi-border text-xs text-ink-muted">
                Rule gate checks enforce zero fraud flags, active policy validity, and claim amount &le; INR 10,000 threshold for automatic straight-through settlement.
              </div>
            </div>
          </div>

          {/* Breakdown Grids */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Claims by Status */}
            <div className="washi-panel p-6">
              <h4 className="font-serif font-bold text-sm text-ink mb-4 pb-2 border-b border-washi-border flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-aoi" />
                Claims by Lifecycle Status
              </h4>
              {metrics.claims_by_status && Object.keys(metrics.claims_by_status).length > 0 ? (
                <div className="space-y-2 text-xs">
                  {Object.entries(metrics.claims_by_status).map(([st, cnt]) => (
                    <div
                      key={st}
                      className="flex items-center justify-between py-1.5 px-3 rounded-lg bg-surface-muted border border-washi-border/60"
                    >
                      <span className="capitalize text-ink font-medium">{st.replace(/_/g, " ")}</span>
                      <span className="font-mono font-bold text-aoi">{cnt}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-ink-muted">No claims logged yet.</p>
              )}
            </div>

            {/* Jobs by Status */}
            <div className="washi-panel p-6">
              <h4 className="font-serif font-bold text-sm text-ink mb-4 pb-2 border-b border-washi-border flex items-center gap-2">
                <Cpu className="w-4 h-4 text-aoi" />
                Ingestion Jobs by Status
              </h4>
              {metrics.jobs_by_status && Object.keys(metrics.jobs_by_status).length > 0 ? (
                <div className="space-y-2 text-xs">
                  {Object.entries(metrics.jobs_by_status).map(([st, cnt]) => (
                    <div
                      key={st}
                      className="flex items-center justify-between py-1.5 px-3 rounded-lg bg-surface-muted border border-washi-border/60"
                    >
                      <span className="capitalize text-ink font-medium">{st.replace(/_/g, " ")}</span>
                      <span className="font-mono font-bold text-status-successText">{cnt}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-ink-muted">No ingestion worker jobs recorded.</p>
              )}
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
