"use client";

import React from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { usePersonaStore } from "@/store/persona-store";
import { queryKeys } from "@/lib/query-keys";
import { getMyPolicies, getMyBilling, getClaims } from "@/lib/api";
import { formatINR, formatDate } from "@/lib/formatters";
import {
  ShieldCheck,
  CreditCard,
  FileCheck2,
  PlusCircle,
  BotMessageSquare,
  ArrowRight,
  Clock,
  Sparkles,
} from "lucide-react";

export default function DashboardPage() {
  const { currentPersonaId, currentUser } = usePersonaStore();

  const { data: policies, isLoading: policiesLoading } = useQuery({
    queryKey: queryKeys.policies(currentPersonaId),
    queryFn: getMyPolicies,
    enabled: currentUser?.role === "customer",
  });

  const { data: billing, isLoading: billingLoading } = useQuery({
    queryKey: queryKeys.billing(currentPersonaId),
    queryFn: getMyBilling,
    enabled: currentUser?.role === "customer",
  });

  const { data: claims, isLoading: claimsLoading } = useQuery({
    queryKey: queryKeys.claims(currentPersonaId, { limit: 5 }),
    queryFn: () => getClaims({ limit: 5 }),
  });

  const activePoliciesCount = Array.isArray(policies)
    ? policies.filter((p) => p.status === "active").length
    : 0;
  const recentClaims = Array.isArray(claims) ? claims.slice(0, 5) : [];

  return (
    <AppShell>
      <PageHeader
        title={`Welcome, ${currentUser?.name}`}
        subtitle={`Role: ${currentUser?.role.toUpperCase()} // Account ID: ${currentPersonaId}`}
        action={
          currentUser?.role === "customer" ? (
            <Link href="/claims/new">
              <Button variant="primary">
                <PlusCircle className="w-4 h-4 mr-2" />
                File New Claim
              </Button>
            </Link>
          ) : currentUser?.role === "adjuster" ? (
            <Link href="/adjuster/queue">
              <Button variant="primary">
                <ShieldCheck className="w-4 h-4 mr-2" />
                View Review Queue
              </Button>
            </Link>
          ) : (
            <Link href="/admin/metrics">
              <Button variant="primary">
                <Sparkles className="w-4 h-4 mr-2" />
                Operations Dashboard
              </Button>
            </Link>
          )
        }
      />

      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
        {/* Policy Card */}
        <div className="washi-panel p-6 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold uppercase tracking-wider text-ink-muted">
              Active Policies
            </span>
            <div className="w-8 h-8 rounded-lg bg-matcha-soft text-status-successText flex items-center justify-center">
              <ShieldCheck className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-3xl font-serif font-bold text-ink mb-1">
              {policiesLoading ? "..." : activePoliciesCount}
            </div>
            <p className="text-xs text-ink-muted">
              {policies?.length ? `Total ${policies.length} subscribed plans` : "No registered policies"}
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-washi-border">
            <Link
              href="/policies"
              className="text-xs font-medium text-aoi hover:text-aoi-deep inline-flex items-center"
            >
              Manage policies <ArrowRight className="w-3 h-3 ml-1" />
            </Link>
          </div>
        </div>

        {/* Billing Card (Customer specific) */}
        <div className="washi-panel p-6 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold uppercase tracking-wider text-ink-muted">
              Billing Due
            </span>
            <div className="w-8 h-8 rounded-lg bg-aoi-wash text-aoi flex items-center justify-center">
              <CreditCard className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-3xl font-serif font-bold text-ink mb-1">
              {billingLoading ? "..." : formatINR(billing?.amount_due_inr)}
            </div>
            <p className="text-xs text-ink-muted flex items-center gap-1">
              <Clock className="w-3 h-3" />
              Due: {formatDate(billing?.due_date)}
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-washi-border">
            <Link
              href="/billing"
              className="text-xs font-medium text-aoi hover:text-aoi-deep inline-flex items-center"
            >
              Billing overview <ArrowRight className="w-3 h-3 ml-1" />
            </Link>
          </div>
        </div>

        {/* Claims Card */}
        <div className="washi-panel p-6 flex flex-col justify-between">
          <div className="flex items-center justify-between mb-4">
            <span className="text-xs font-semibold uppercase tracking-wider text-ink-muted">
              Active Claims
            </span>
            <div className="w-8 h-8 rounded-lg bg-sakura-soft text-ink-muted flex items-center justify-center">
              <FileCheck2 className="w-4 h-4" />
            </div>
          </div>
          <div>
            <div className="text-3xl font-serif font-bold text-ink mb-1">
              {claimsLoading ? "..." : claims?.length ?? 0}
            </div>
            <p className="text-xs text-ink-muted">
              {claims?.length ? "In process or evaluated" : "No open claims"}
            </p>
          </div>
          <div className="mt-4 pt-3 border-t border-washi-border">
            <Link
              href="/claims"
              className="text-xs font-medium text-aoi hover:text-aoi-deep inline-flex items-center"
            >
              View all claims <ArrowRight className="w-3 h-3 ml-1" />
            </Link>
          </div>
        </div>
      </div>

      {/* Quick Action Banner */}
      <div className="washi-panel p-6 mb-8 bg-gradient-to-r from-aoi-wash/50 via-surface to-sakura-soft/30 border border-aoi/20">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-xl bg-aoi text-white flex items-center justify-center shrink-0 shadow-sm">
              <BotMessageSquare className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-serif font-bold text-base text-ink">
                Need coverage clarification or claim assistance?
              </h3>
              <p className="text-xs text-ink-muted">
                Our AI Assistant searches verified policy clauses with page citations and assists in FNOL.
              </p>
            </div>
          </div>
          <Link href="/assistant">
            <Button variant="primary" size="sm">
              Open AI Assistant
            </Button>
          </Link>
        </div>
      </div>

      {/* Recent Claims Section */}
      <div className="washi-panel p-6">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-washi-border">
          <div>
            <h2 className="font-serif font-bold text-lg text-ink">Recent Claims</h2>
            <p className="text-xs text-ink-muted">Overview of claims filed or assigned under this profile</p>
          </div>
          <Link href="/claims" className="text-xs text-aoi font-medium hover:underline">
            View all ({claims?.length || 0})
          </Link>
        </div>

        {claimsLoading ? (
          <div className="space-y-3 py-4">
            <div className="h-10 skeleton w-full" />
            <div className="h-10 skeleton w-full" />
            <div className="h-10 skeleton w-full" />
          </div>
        ) : recentClaims.length === 0 ? (
          <div className="text-center py-8 text-sm text-ink-muted">
            No claims filed yet. Click "File New Claim" above to report a first notice of loss.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-washi-border text-ink-muted uppercase tracking-wider font-semibold">
                  <th className="py-2.5 px-3">Claim Number</th>
                  <th className="py-2.5 px-3">Incident Type</th>
                  <th className="py-2.5 px-3">Incident Date</th>
                  <th className="py-2.5 px-3">Requested</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-washi-border/60">
                {recentClaims.map((claim) => (
                  <tr key={claim.public_id} className="hover:bg-surface-muted/50 transition-colors">
                    <td className="py-3 px-3 font-mono font-medium text-ink">
                      {claim.claim_number}
                    </td>
                    <td className="py-3 px-3 capitalize">{claim.incident_type.replace(/_/g, " ")}</td>
                    <td className="py-3 px-3 text-ink-muted">{formatDate(claim.incident_date)}</td>
                    <td className="py-3 px-3 font-medium text-ink">
                      {formatINR(claim.requested_amount_inr)}
                    </td>
                    <td className="py-3 px-3">
                      <StatusBadge status={claim.status} />
                    </td>
                    <td className="py-3 px-3 text-right">
                      <Link
                        href={`/claims/${claim.public_id}`}
                        className="text-aoi font-medium hover:underline inline-flex items-center"
                      >
                        Details <ArrowRight className="w-3 h-3 ml-1" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </AppShell>
  );
}
