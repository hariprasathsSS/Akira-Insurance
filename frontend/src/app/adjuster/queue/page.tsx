"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { usePersonaStore } from "@/store/persona-store";
import { queryKeys } from "@/lib/query-keys";
import { getClaims } from "@/lib/api";
import { formatINR, formatDate } from "@/lib/formatters";
import { ShieldCheck, ShieldAlert, ArrowRight, Zap, Filter } from "lucide-react";

const QUEUE_TABS = [
  { label: "All Active Queue", value: "" },
  { label: "Submitted", value: "submitted" },
  { label: "Under Review", value: "under_review" },
  { label: "Evaluated", value: "evaluated" },
];

export default function AdjusterQueuePage() {
  const { currentPersonaId } = usePersonaStore();
  const [activeTab, setActiveTab] = useState<string>("");

  const { data: claims, isLoading, error, refetch } = useQuery({
    queryKey: queryKeys.adjusterQueue(currentPersonaId, activeTab),
    queryFn: () => getClaims({ status: activeTab || undefined }),
  });

  return (
    <AppShell>
      <PageHeader
        title="Adjuster Claims Review Queue"
        subtitle="Manage pending claims, trigger deterministic rule evaluations, and authorize settlement payouts."
      />

      {/* Status Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-4 mb-6 border-b border-washi-border no-scrollbar text-xs">
        <span className="text-ink-muted flex items-center gap-1 mr-2 font-medium">
          <Filter className="w-3.5 h-3.5" /> Stage:
        </span>
        {QUEUE_TABS.map((tab) => {
          const isActive = activeTab === tab.value;
          return (
            <button
              key={tab.value}
              onClick={() => setActiveTab(tab.value)}
              className={`px-3 py-1.5 rounded-lg whitespace-nowrap transition-colors font-medium ${
                isActive
                  ? "bg-aoi text-white shadow-xs"
                  : "bg-surface text-ink-muted hover:text-ink hover:bg-surface-muted border border-washi-border"
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {isLoading ? (
        <div className="space-y-4">
          <div className="h-16 skeleton washi-panel" />
          <div className="h-16 skeleton washi-panel" />
          <div className="h-16 skeleton washi-panel" />
        </div>
      ) : error ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : !claims || claims.length === 0 ? (
        <EmptyState
          title="Review Queue Clear"
          description="There are currently no claims pending adjudication in this status tab."
        />
      ) : (
        <div className="washi-panel overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-washi-border bg-surface-muted text-ink-muted uppercase tracking-wider font-semibold">
                  <th className="py-3 px-4">Claim Reference</th>
                  <th className="py-3 px-4">Claimant / Policy</th>
                  <th className="py-3 px-4">Incident Info</th>
                  <th className="py-3 px-4">Claimed Amount</th>
                  <th className="py-3 px-4">AI Rec Payout</th>
                  <th className="py-3 px-4">Flags</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Adjudication</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-washi-border/60">
                {claims.map((claim) => (
                  <tr key={claim.public_id} className="hover:bg-surface-muted/50 transition-colors">
                    <td className="py-3.5 px-4">
                      <div className="font-mono font-bold text-ink text-sm">
                        {claim.claim_number}
                      </div>
                      <div className="font-mono text-[10px] text-ink-muted">
                        ID: {claim.public_id}
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="font-mono font-medium text-ink">
                        {claim.customer_user_id}
                      </div>
                      <div className="font-mono text-[11px] text-ink-muted">
                        {claim.policy_public_id}
                      </div>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="font-medium text-ink capitalize">
                        {claim.incident_type.replace(/_/g, " ")}
                      </div>
                      <div className="text-ink-muted text-[11px]">
                        {formatDate(claim.incident_date)}
                      </div>
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-ink">
                      {formatINR(claim.requested_amount_inr)}
                    </td>
                    <td className="py-3.5 px-4 font-mono">
                      {claim.calculated_payout_inr !== null && claim.calculated_payout_inr !== undefined ? (
                        <span className="text-aoi font-bold">
                          {formatINR(claim.calculated_payout_inr)}
                        </span>
                      ) : (
                        <span className="text-ink-muted italic">Not calculated</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 space-y-1">
                      {claim.fraud_flag && (
                        <span className="inline-flex items-center gap-1 text-[10px] text-status-dangerText font-semibold bg-status-dangerSoft px-1.5 py-0.5 rounded border border-status-dangerText/30">
                          <ShieldAlert className="w-3 h-3" /> Fraud Suspect
                        </span>
                      )}
                      {claim.stp_eligible && (
                        <span className="inline-flex items-center gap-1 text-[10px] text-status-successText font-semibold bg-matcha-soft px-1.5 py-0.5 rounded border border-matcha/40">
                          <Zap className="w-3 h-3" /> STP Eligible
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      <StatusBadge status={claim.status} />
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Link
                        href={`/adjuster/claims/${claim.public_id}`}
                        className="inline-flex items-center gap-1 text-xs font-semibold text-aoi hover:text-aoi-deep bg-aoi-wash px-3 py-1.5 rounded-lg transition-colors"
                      >
                        Open Console <ArrowRight className="w-3 h-3" />
                      </Link>
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
