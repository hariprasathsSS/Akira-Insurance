"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { usePersonaStore } from "@/store/persona-store";
import { queryKeys } from "@/lib/query-keys";
import { getClaims } from "@/lib/api";
import { formatINR, formatDate } from "@/lib/formatters";
import { PlusCircle, ArrowRight, ShieldAlert, Filter } from "lucide-react";

const STATUS_FILTERS = [
  { label: "All", value: "" },
  { label: "Submitted", value: "submitted" },
  { label: "Under Review", value: "under_review" },
  { label: "Evaluated", value: "evaluated" },
  { label: "Approved", value: "approved" },
  { label: "Denied", value: "denied" },
  { label: "Closed", value: "closed" },
];

export default function ClaimsPage() {
  const { currentPersonaId, currentUser } = usePersonaStore();
  const [selectedStatus, setSelectedStatus] = useState<string>("");

  const { data: claims, isLoading, error, refetch } = useQuery({
    queryKey: queryKeys.claims(currentPersonaId, { status: selectedStatus }),
    queryFn: () => getClaims({ status: selectedStatus || undefined }),
  });

  return (
    <AppShell>
      <PageHeader
        title="Insurance Claims Directory"
        subtitle="Track first notices of loss, lifecycle states, payouts, and adjuster decisions."
        action={
          currentUser?.role === "customer" && (
            <Link href="/claims/new">
              <Button variant="primary">
                <PlusCircle className="w-4 h-4 mr-2" />
                File New Claim
              </Button>
            </Link>
          )
        }
      />

      {/* Filter Tabs */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-4 mb-6 border-b border-washi-border no-scrollbar text-xs">
        <span className="text-ink-muted flex items-center gap-1 mr-2 font-medium">
          <Filter className="w-3.5 h-3.5" /> Filter:
        </span>
        {STATUS_FILTERS.map((tab) => {
          const isActive = selectedStatus === tab.value;
          return (
            <button
              key={tab.value}
              onClick={() => setSelectedStatus(tab.value)}
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
      ) : !claims || !Array.isArray(claims) || claims.length === 0 ? (
        <EmptyState
          title="No Claims Found"
          description={
            selectedStatus
              ? `There are no claims currently in "${selectedStatus.replace(/_/g, " ")}" status.`
              : "No insurance claims recorded for this user profile."
          }
          actionText={currentUser?.role === "customer" ? "File a New Claim" : undefined}
          onAction={currentUser?.role === "customer" ? () => window.location.href = "/claims/new" : undefined}
        />
      ) : (
        <div className="washi-panel overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-washi-border bg-surface-muted text-ink-muted uppercase tracking-wider font-semibold">
                  <th className="py-3 px-4">Claim ID / Number</th>
                  <th className="py-3 px-4">Incident Info</th>
                  <th className="py-3 px-4">Incident Date</th>
                  <th className="py-3 px-4">Requested Amount</th>
                  <th className="py-3 px-4">Payout (Calc / Appr)</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-washi-border/60">
                {claims.map((claim) => (
                  <tr key={claim.public_id} className="hover:bg-surface-muted/50 transition-colors">
                    <td className="py-3.5 px-4">
                      <div className="font-mono font-semibold text-ink text-sm">
                        {claim.claim_number}
                      </div>
                      <div className="font-mono text-[10px] text-ink-muted">
                        Ref: {claim.public_id}
                      </div>
                      {claim.fraud_flag && (
                        <span className="inline-flex items-center gap-1 mt-1 text-[10px] text-status-dangerText font-semibold bg-status-dangerSoft px-1.5 py-0.5 rounded border border-status-dangerText/30">
                          <ShieldAlert className="w-3 h-3" /> Fraud Review
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="font-medium text-ink capitalize">
                        {claim.incident_type.replace(/_/g, " ")}
                      </div>
                      <div className="text-ink-muted text-[11px] line-clamp-1 max-w-xs">
                        {claim.incident_description}
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-ink-muted">
                      {formatDate(claim.incident_date)}
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-ink">
                      {formatINR(claim.requested_amount_inr)}
                    </td>
                    <td className="py-3.5 px-4 font-mono">
                      {claim.approved_payout_inr !== null && claim.approved_payout_inr !== undefined ? (
                        <span className="text-status-successText font-semibold">
                          {formatINR(claim.approved_payout_inr)} (Final)
                        </span>
                      ) : claim.calculated_payout_inr !== null && claim.calculated_payout_inr !== undefined ? (
                        <span className="text-aoi font-medium">
                          {formatINR(claim.calculated_payout_inr)} (AI Rec)
                        </span>
                      ) : (
                        <span className="text-ink-muted italic">Pending review</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      <StatusBadge status={claim.status} />
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Link
                        href={
                          currentUser?.role === "adjuster" || currentUser?.role === "admin"
                            ? `/adjuster/claims/${claim.public_id}`
                            : `/claims/${claim.public_id}`
                        }
                        className="inline-flex items-center text-aoi font-medium hover:text-aoi-deep hover:underline"
                      >
                        {currentUser?.role === "adjuster" ? "Console" : "Timeline"}
                        <ArrowRight className="w-3 h-3 ml-1" />
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
