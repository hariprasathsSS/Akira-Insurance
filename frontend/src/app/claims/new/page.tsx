"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { Button } from "@/components/ui/Button";
import { usePersonaStore } from "@/store/persona-store";
import { queryKeys } from "@/lib/query-keys";
import { getMyPolicies, createClaim, CreateClaimPayload } from "@/lib/api";
import { ApiError } from "@/lib/api/errors";
import { formatINR } from "@/lib/formatters";
import { CheckCircle2, AlertCircle, ArrowLeft, ArrowRight, ShieldCheck, KeyRound } from "lucide-react";

const fnolSchema = z.object({
  policy_public_id: z.string().min(1, "Please select an applicable insurance policy."),
  incident_type: z.string().min(1, "Please specify the incident type."),
  incident_date: z.string().min(1, "Incident date is required."),
  incident_location: z.string().min(2, "Incident location is required."),
  incident_description: z.string().min(10, "Please provide a detailed description (min 10 characters)."),
  requested_amount: z.coerce.number().positive("Requested amount must be greater than zero."),
});

type FnolFormData = z.infer<typeof fnolSchema>;

export default function NewClaimPage() {
  const { currentPersonaId } = usePersonaStore();
  const queryClient = useQueryClient();

  // Stable UUID v4 idempotency key across retries
  const [idempotencyKey] = useState<string>(() =>
    typeof crypto !== "undefined" && crypto.randomUUID ? crypto.randomUUID() : `fnol-${Date.now()}`
  );

  const [submittedClaim, setSubmittedClaim] = useState<{ claim_number: string; public_id: string } | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const { data: policies, isLoading: policiesLoading } = useQuery({
    queryKey: queryKeys.policies(currentPersonaId),
    queryFn: getMyPolicies,
  });

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FnolFormData>({
    resolver: zodResolver(fnolSchema),
    defaultValues: {
      incident_date: new Date().toISOString().split("T")[0],
    },
  });

  const claimMutation = useMutation({
    mutationFn: (data: FnolFormData) => {
      const payload: CreateClaimPayload = {
        policy_public_id: data.policy_public_id,
        incident_type: data.incident_type,
        incident_date: data.incident_date,
        incident_location: data.incident_location,
        incident_description: data.incident_description,
        requested_amount: data.requested_amount,
        idempotency_key: idempotencyKey,
      };
      return createClaim(payload);
    },
    onSuccess: (newClaim) => {
      setSubmittedClaim({
        claim_number: newClaim.claim_number,
        public_id: newClaim.public_id,
      });
      // Invalidate claims list query cache
      queryClient.invalidateQueries({ queryKey: ["claims", currentPersonaId] });
    },
    onError: (err: ApiError | Error) => {
      setSubmitError(err.message || "Failed to submit claim. Please check details and try again.");
    },
  });

  const onSubmit = (data: FnolFormData) => {
    setSubmitError(null);
    claimMutation.mutate(data);
  };

  return (
    <AppShell>
      <div className="max-w-3xl mx-auto">
        <div className="mb-4">
          <Link
            href="/claims"
            className="text-xs text-ink-muted hover:text-ink inline-flex items-center gap-1 font-medium transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Back to claims directory
          </Link>
        </div>

        <PageHeader
          title="First Notice of Loss (FNOL)"
          subtitle="Submit an initial insurance claim for automated review and adjuster assignment."
        />

        {submittedClaim ? (
          <div className="washi-panel p-8 text-center bg-matcha-soft/30 border-matcha animate-in fade-in zoom-in-95">
            <div className="w-14 h-14 rounded-full bg-matcha-soft border border-[#B8C8AD] flex items-center justify-center text-status-successText mx-auto mb-4">
              <CheckCircle2 className="w-8 h-8" />
            </div>
            <h2 className="font-serif text-2xl font-bold text-ink mb-2">Claim Filed Successfully</h2>
            <p className="text-sm text-ink-muted mb-6">
              Your claim has been recorded and submitted into the adjudicator queue.
            </p>
            <div className="p-4 rounded-xl bg-surface border border-washi-border inline-block text-left mb-6 font-mono text-xs">
              <div>Claim Number: <strong className="text-ink text-sm">{submittedClaim.claim_number}</strong></div>
              <div className="text-ink-muted mt-1">Reference ID: {submittedClaim.public_id}</div>
              <div className="text-ink-muted mt-1">Idempotency Key: {idempotencyKey}</div>
            </div>
            <div className="flex items-center justify-center gap-4">
              <Link href={`/claims/${submittedClaim.public_id}`}>
                <Button variant="primary">
                  Track Claim Lifecycle <ArrowRight className="w-4 h-4 ml-1.5" />
                </Button>
              </Link>
              <Link href="/claims">
                <Button variant="secondary">View All Claims</Button>
              </Link>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="washi-panel p-6 sm:p-8 space-y-6">
            {submitError && (
              <div className="p-4 rounded-lg bg-status-dangerSoft border border-status-dangerText/30 text-status-dangerText text-xs flex items-start gap-2.5">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <div>
                  <div className="font-semibold">Submission Error</div>
                  <div>{submitError}</div>
                </div>
              </div>
            )}

            {/* Idempotency Key Notice */}
            <div className="px-3.5 py-2 rounded-lg bg-surface-muted border border-washi-border flex items-center justify-between text-[11px] text-ink-muted font-mono">
              <span className="flex items-center gap-1.5">
                <KeyRound className="w-3.5 h-3.5 text-aoi" />
                Safe Idempotency Token:
              </span>
              <span className="truncate max-w-[200px] sm:max-w-none">{idempotencyKey}</span>
            </div>

            {/* Policy Selector */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-ink mb-1.5">
                Select Insured Policy *
              </label>
              {policiesLoading ? (
                <div className="h-10 skeleton w-full" />
              ) : (
                <select
                  {...register("policy_public_id")}
                  className="w-full px-3.5 py-2 text-sm rounded-lg border border-washi-border bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-aoi focus:border-aoi transition-all"
                >
                  <option value="">-- Choose active policy --</option>
                  {Array.isArray(policies) &&
                    policies.map((policy) => (
                      <option key={policy.public_id} value={policy.public_id}>
                        {policy.title} ({policy.policy_number}) — Limit: {formatINR(policy.max_coverage_inr)}
                      </option>
                    ))}
                </select>
              )}
              {errors.policy_public_id && (
                <p className="mt-1 text-xs text-status-dangerText">{errors.policy_public_id.message}</p>
              )}
            </div>

            {/* Incident Type & Date */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-ink mb-1.5">
                  Incident Type *
                </label>
                <select
                  {...register("incident_type")}
                  className="w-full px-3.5 py-2 text-sm rounded-lg border border-washi-border bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-aoi focus:border-aoi transition-all capitalize"
                >
                  <option value="">-- Select incident type --</option>
                  <option value="hospitalization">Hospitalization / Inpatient Care</option>
                  <option value="day_care_surgery">Day Care Surgical Procedure</option>
                  <option value="collision">Vehicle Collision Damage</option>
                  <option value="water_damage">Home Plumbing / Water Damage</option>
                  <option value="theft">Theft / Property Loss</option>
                  <option value="critical_illness">Critical Illness Diagnosis</option>
                </select>
                {errors.incident_type && (
                  <p className="mt-1 text-xs text-status-dangerText">{errors.incident_type.message}</p>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-ink mb-1.5">
                  Incident Date *
                </label>
                <input
                  type="date"
                  {...register("incident_date")}
                  className="w-full px-3.5 py-2 text-sm rounded-lg border border-washi-border bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-aoi focus:border-aoi transition-all"
                />
                {errors.incident_date && (
                  <p className="mt-1 text-xs text-status-dangerText">{errors.incident_date.message}</p>
                )}
              </div>
            </div>

            {/* Incident Location & Requested Amount */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-ink mb-1.5">
                  Location of Occurrence *
                </label>
                <input
                  type="text"
                  placeholder="e.g. City Hospital, Sector 12 or Street Address"
                  {...register("incident_location")}
                  className="w-full px-3.5 py-2 text-sm rounded-lg border border-washi-border bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-aoi focus:border-aoi transition-all"
                />
                {errors.incident_location && (
                  <p className="mt-1 text-xs text-status-dangerText">{errors.incident_location.message}</p>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-ink mb-1.5">
                  Estimated / Claimed Amount (INR) *
                </label>
                <input
                  type="number"
                  step="any"
                  placeholder="e.g. 35000"
                  {...register("requested_amount")}
                  className="w-full px-3.5 py-2 text-sm rounded-lg border border-washi-border bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-aoi focus:border-aoi transition-all font-mono"
                />
                {errors.requested_amount && (
                  <p className="mt-1 text-xs text-status-dangerText">{errors.requested_amount.message}</p>
                )}
              </div>
            </div>

            {/* Description */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-ink mb-1.5">
                Incident Summary & Circumstances *
              </label>
              <textarea
                rows={4}
                placeholder="Describe what occurred, medical treatment received, emergency services engaged, or property damaged..."
                {...register("incident_description")}
                className="w-full px-3.5 py-2 text-sm rounded-lg border border-washi-border bg-surface text-ink focus:outline-none focus:ring-2 focus:ring-aoi focus:border-aoi transition-all leading-relaxed"
              />
              {errors.incident_description && (
                <p className="mt-1 text-xs text-status-dangerText">{errors.incident_description.message}</p>
              )}
            </div>

            {/* Actions */}
            <div className="pt-4 border-t border-washi-border flex items-center justify-between">
              <span className="text-xs text-ink-muted">
                * Required fields for deterministic rules validation
              </span>
              <Button type="submit" variant="primary" isLoading={isSubmitting || claimMutation.isPending}>
                <ShieldCheck className="w-4 h-4 mr-2" />
                Submit Claim for Evaluation
              </Button>
            </div>
          </form>
        )}
      </div>
    </AppShell>
  );
}
