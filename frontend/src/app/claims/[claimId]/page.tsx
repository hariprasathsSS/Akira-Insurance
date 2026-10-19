"use client";

import React from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ErrorState } from "@/components/ui/ErrorState";
import { usePersonaStore } from "@/store/persona-store";
import { queryKeys } from "@/lib/query-keys";
import { getClaim, getClaimEvents } from "@/lib/api";
import { formatINR, formatDate, formatDateTime } from "@/lib/formatters";
import { ArrowLeft, Clock, ShieldAlert, CheckCircle2, User, FileText, Activity } from "lucide-react";

export default function ClaimDetailPage() {
  const params = useParams();
  const claimId = params.claimId as string;
  const { currentPersonaId, currentUser } = usePersonaStore();

  const {
    data: claim,
    isLoading: claimLoading,
    error: claimError,
    refetch: refetchClaim,
  } = useQuery({
    queryKey: queryKeys.claim(currentPersonaId, claimId),
    queryFn: () => getClaim(claimId),
  });

  const {
    data: events,
    isLoading: eventsLoading,
    error: eventsError,
  } = useQuery({
    queryKey: queryKeys.claimEvents(currentPersonaId, claimId),
    queryFn: () => getClaimEvents(claimId),
  });

  if (claimLoading) {
    return (
      <AppShell>
        <div className="space-y-6">
          <div className="h-20 skeleton washi-panel" />
          <div className="h-64 skeleton washi-panel" />
        </div>
      </AppShell>
    );
  }

  if (claimError || !claim) {
    return (
      <AppShell>
        <ErrorState error={claimError} onRetry={refetchClaim} title="Claim Not Found" />
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="mb-4">
        <Link
          href="/claims"
          className="text-xs text-ink-muted hover:text-ink inline-flex items-center gap-1 font-medium transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to claims directory
        </Link>
      </div>

      <PageHeader
        title={`Claim: ${claim.claim_number}`}
        subtitle={`Reference ID: ${claim.public_id} // Policy: ${claim.policy_public_id}`}
        action={<StatusBadge status={claim.status} />}
      />

      {/* Fraud Flag Alert */}
      {claim.fraud_flag && (
        <div className="mb-6 p-4 rounded-xl bg-status-dangerSoft border border-status-dangerText/30 text-xs text-status-dangerText flex items-center gap-3">
          <ShieldAlert className="w-5 h-5 shrink-0" />
          <div>
            <span className="font-bold">Fraud Review Sentinel Active:</span> This claim has been flagged by automated underwriting checks and requires senior adjuster verification before payout authorization.
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Facts & Payouts */}
        <div className="lg:col-span-2 space-y-6">
          {/* Claim Summary Card */}
          <div className="washi-panel p-6">
            <h3 className="font-serif font-bold text-base text-ink mb-4 pb-2 border-b border-washi-border flex items-center gap-2">
              <FileText className="w-4 h-4 text-aoi" />
              Claim Incident Facts
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs mb-4">
              <div>
                <span className="text-ink-muted block mb-0.5">Incident Type</span>
                <span className="font-medium text-ink capitalize text-sm">
                  {claim.incident_type.replace(/_/g, " ")}
                </span>
              </div>
              <div>
                <span className="text-ink-muted block mb-0.5">Date of Occurrence</span>
                <span className="font-medium text-ink text-sm">
                  {formatDate(claim.incident_date)}
                </span>
              </div>
              <div>
                <span className="text-ink-muted block mb-0.5">Location</span>
                <span className="font-medium text-ink">{claim.incident_location}</span>
              </div>
              <div>
                <span className="text-ink-muted block mb-0.5">Submission Timestamp</span>
                <span className="font-medium text-ink">{formatDateTime(claim.created_at)}</span>
              </div>
            </div>

            <div className="pt-3 border-t border-washi-border">
              <span className="text-xs text-ink-muted block mb-1">Incident Summary</span>
              <p className="text-xs text-ink bg-surface-muted p-3.5 rounded-lg border border-washi-border leading-relaxed">
                {claim.incident_description}
              </p>
            </div>
          </div>

          {/* Settlement & Payout Summary Card */}
          <div className="washi-panel p-6">
            <h3 className="font-serif font-bold text-base text-ink mb-4 pb-2 border-b border-washi-border flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-aoi" />
              Settlement & Financial Breakdown
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="p-4 rounded-xl bg-surface-muted border border-washi-border">
                <span className="text-[11px] uppercase tracking-wider text-ink-muted font-semibold block mb-1">
                  Requested Amount
                </span>
                <span className="font-serif text-lg font-bold text-ink">
                  {formatINR(claim.requested_amount_inr)}
                </span>
              </div>

              <div className="p-4 rounded-xl bg-aoi-wash/40 border border-aoi/20">
                <span className="text-[11px] uppercase tracking-wider text-aoi font-semibold block mb-1">
                  AI Recommended Payout
                </span>
                <span className="font-serif text-lg font-bold text-aoi">
                  {formatINR(claim.calculated_payout_inr, "Pending review")}
                </span>
              </div>

              <div className="p-4 rounded-xl bg-matcha-soft/40 border border-[#B8C8AD]/60">
                <span className="text-[11px] uppercase tracking-wider text-status-successText font-semibold block mb-1">
                  Approved Settlement
                </span>
                <span className="font-serif text-lg font-bold text-status-successText">
                  {formatINR(claim.approved_payout_inr, "Not finalized")}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Lifecycle Timeline */}
        <div className="space-y-6">
          <div className="washi-panel p-6">
            <h3 className="font-serif font-bold text-base text-ink mb-4 pb-2 border-b border-washi-border flex items-center gap-2">
              <Activity className="w-4 h-4 text-aoi" />
              Lifecycle Audit Timeline
            </h3>

            {eventsLoading ? (
              <div className="space-y-3">
                <div className="h-12 skeleton w-full" />
                <div className="h-12 skeleton w-full" />
              </div>
            ) : !events || events.length === 0 ? (
              <p className="text-xs text-ink-muted">No state transition records available.</p>
            ) : (
              <div className="relative pl-6 space-y-6 before:content-[''] before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-washi-border">
                {events.map((evt) => (
                  <div key={evt.id} className="relative text-xs">
                    <span className="absolute -left-6 top-0.5 w-4 h-4 rounded-full bg-surface border-2 border-aoi flex items-center justify-center">
                      <span className="w-1.5 h-1.5 rounded-full bg-aoi" />
                    </span>
                    <div className="font-semibold text-ink flex items-center gap-2">
                      <span className="capitalize">{evt.to_status.replace(/_/g, " ")}</span>
                      {evt.from_status && (
                        <span className="text-[10px] text-ink-muted font-normal">
                          (from {evt.from_status})
                        </span>
                      )}
                    </div>
                    {evt.reason && (
                      <p className="text-[11px] text-ink-muted mt-1 bg-surface-muted p-2 rounded border border-washi-border">
                        {evt.reason}
                      </p>
                    )}
                    <div className="flex items-center gap-2 mt-1 text-[10px] text-ink-muted">
                      <Clock className="w-3 h-3" />
                      <span>{formatDateTime(evt.created_at)}</span>
                      {evt.triggered_by_user_id && (
                        <>
                          <span>•</span>
                          <span className="font-mono">{evt.triggered_by_user_id}</span>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
