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
import { getMyPolicies } from "@/lib/api";
import { formatINR, formatDate } from "@/lib/formatters";
import { Shield, Calendar, DollarSign } from "lucide-react";

export default function PoliciesPage() {
  const { currentPersonaId } = usePersonaStore();

  const { data: policies, isLoading, error, refetch } = useQuery({
    queryKey: queryKeys.policies(currentPersonaId),
    queryFn: getMyPolicies,
  });

  return (
    <AppShell>
      <PageHeader
        title="Insurance Policies"
        subtitle="Active coverages, policy limits, deductibles, and validity periods."
      />

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="h-48 skeleton washi-panel" />
          <div className="h-48 skeleton washi-panel" />
        </div>
      ) : error ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : !policies || !Array.isArray(policies) || policies.length === 0 ? (
        <EmptyState
          title="No Policies Registered"
          description="There are currently no active insurance policies linked to this persona."
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {policies.map((policy) => (
            <div key={policy.public_id} className="washi-panel p-6 flex flex-col justify-between">
              <div>
                <div className="flex items-start justify-between gap-4 mb-3">
                  <div>
                    <span className="text-[10px] uppercase tracking-wider font-mono px-2 py-0.5 rounded bg-surface-muted text-ink-muted border border-washi-border">
                      {policy.policy_type} // {policy.plan_tier} tier
                    </span>
                    <h3 className="font-serif text-lg font-bold text-ink mt-2">
                      {policy.title}
                    </h3>
                    <p className="text-xs font-mono text-ink-muted mt-0.5">
                      No: {policy.policy_number}
                    </p>
                  </div>
                  <StatusBadge status={policy.status} />
                </div>

                <div className="grid grid-cols-2 gap-4 my-5 p-3 rounded-xl bg-surface-muted border border-washi-border text-xs">
                  <div>
                    <div className="text-ink-muted flex items-center gap-1 mb-1">
                      <DollarSign className="w-3.5 h-3.5" />
                      <span>Max Coverage</span>
                    </div>
                    <div className="font-semibold text-ink text-sm">
                      {formatINR(policy.max_coverage_inr)}
                    </div>
                  </div>
                  <div>
                    <div className="text-ink-muted flex items-center gap-1 mb-1">
                      <Shield className="w-3.5 h-3.5" />
                      <span>Deductible</span>
                    </div>
                    <div className="font-semibold text-ink text-sm">
                      {formatINR(policy.deductible_inr)}
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-washi-border flex items-center justify-between text-xs text-ink-muted">
                <div className="flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5" />
                  <span>Valid: {formatDate(policy.effective_from)} - {formatDate(policy.effective_to)}</span>
                </div>
                <span className="font-mono text-[11px]">ID: {policy.public_id}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </AppShell>
  );
}
