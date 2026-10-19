"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { usePersonaStore } from "@/store/persona-store";
import { queryKeys } from "@/lib/query-keys";
import { getMyBilling } from "@/lib/api";
import { formatINR, formatDate } from "@/lib/formatters";
import { CreditCard, Calendar, CheckCircle2, Info } from "lucide-react";

export default function BillingPage() {
  const { currentPersonaId } = usePersonaStore();

  const { data: billing, isLoading, error, refetch } = useQuery({
    queryKey: queryKeys.billing(currentPersonaId),
    queryFn: getMyBilling,
  });

  return (
    <AppShell>
      <PageHeader
        title="Billing & Premium Status"
        subtitle="Policy premium schedules, amounts due, and payment settlement records."
      />

      {isLoading ? (
        <div className="h-64 skeleton washi-panel max-w-2xl mx-auto" />
      ) : error ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : !billing ? (
        <EmptyState
          title="No Billing Account"
          description="There is no active premium billing account found for this user."
        />
      ) : (
        <div className="max-w-2xl mx-auto space-y-6">
          <div className="washi-panel p-6 sm:p-8">
            <div className="flex items-start justify-between pb-6 border-b border-washi-border">
              <div>
                <span className="text-[10px] uppercase tracking-wider font-mono px-2 py-0.5 rounded bg-surface-muted text-ink-muted border border-washi-border">
                  Policy Account: {billing.policy_public_id}
                </span>
                <h3 className="font-serif text-xl font-bold text-ink mt-2">
                  Premium Statement
                </h3>
              </div>
              <StatusBadge status={billing.status} />
            </div>

            <div className="my-6 p-6 rounded-xl bg-surface-muted border border-washi-border flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <span className="text-xs uppercase tracking-wider text-ink-muted font-semibold">
                  Amount Due
                </span>
                <div className="text-3xl font-serif font-bold text-ink mt-1">
                  {formatINR(billing.amount_due_inr)}
                </div>
              </div>
              <div className="sm:text-right">
                <span className="text-xs uppercase tracking-wider text-ink-muted font-semibold flex items-center sm:justify-end gap-1">
                  <Calendar className="w-3.5 h-3.5" />
                  Due Date
                </span>
                <div className="text-sm font-semibold text-ink mt-1">
                  {formatDate(billing.due_date)}
                </div>
              </div>
            </div>

            <div className="space-y-3 text-xs text-ink-muted pt-2">
              <div className="flex items-center justify-between py-2 border-b border-washi-border/60">
                <span className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-status-successText" />
                  Last Recorded Payment
                </span>
                <span className="font-semibold text-ink">
                  {formatINR(billing.last_payment_amount_inr, "No prior payments")}
                </span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-washi-border/60">
                <span className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-ink-muted" />
                  Last Payment Date
                </span>
                <span className="font-mono text-ink">
                  {formatDate(billing.last_payment_date)}
                </span>
              </div>
              <div className="flex items-center justify-between py-2">
                <span>Account Reference</span>
                <span className="font-mono text-[11px] text-ink-muted">{billing.public_id}</span>
              </div>
            </div>

            {/* Contract Notice */}
            <div className="mt-8 p-3 rounded-lg bg-surface-muted/60 border border-washi-border text-[11px] text-ink-muted flex items-start gap-2">
              <Info className="w-4 h-4 text-aoi shrink-0 mt-0.5" />
              <span>
                <strong>POC Contract Note:</strong> Billing records reflect server-synchronized state. Direct payment settlement integration is managed through automated carrier banking workflows; no manual web checkout is required.
              </span>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
