"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { ErrorState } from "@/components/ui/ErrorState";
import { usePersonaStore } from "@/store/persona-store";
import { queryKeys } from "@/lib/query-keys";
import {
  getClaim,
  getAdjusterNotes,
  addAdjusterNote,
  evaluateClaim,
  getClaimEvaluations,
  submitClaimDecision,
} from "@/lib/api";
import { formatINR, formatDate, formatDateTime } from "@/lib/formatters";
import {
  ArrowLeft,
  MessageSquare,
  Sparkles,
  CheckCircle2,
  XCircle,
  HelpCircle,
  FileText,
  ShieldAlert,
  Calculator,
  Send,
  RefreshCw,
  AlertTriangle,
} from "lucide-react";

export default function AdjusterClaimConsolePage() {
  const params = useParams();
  const claimId = params.claimId as string;
  const { currentPersonaId, currentUser } = usePersonaStore();
  const queryClient = useQueryClient();

  // Internal Note form state
  const [noteText, setNoteText] = useState("");

  // Decision Modal / Form state
  const [decisionType, setDecisionType] = useState<"approved" | "denied" | "request_information">("approved");
  const [approvedAmount, setApprovedAmount] = useState<string>("");
  const [decisionReason, setDecisionReason] = useState<string>("");
  const [decisionSuccessMsg, setDecisionSuccessMsg] = useState<string | null>(null);

  // Queries
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
    data: notes,
    isLoading: notesLoading,
    refetch: refetchNotes,
  } = useQuery({
    queryKey: queryKeys.adjusterNotes(currentPersonaId, claimId),
    queryFn: () => getAdjusterNotes(claimId),
  });

  const {
    data: evaluations,
    isLoading: evalsLoading,
    refetch: refetchEvals,
  } = useQuery({
    queryKey: queryKeys.adjusterEvaluations(currentPersonaId, claimId),
    queryFn: () => getClaimEvaluations(claimId),
  });

  const latestEvaluation = evaluations && evaluations.length > 0 ? evaluations[0] : null;

  // Mutations
  const addNoteMutation = useMutation({
    mutationFn: (text: string) => addAdjusterNote(claimId, text),
    onSuccess: () => {
      setNoteText("");
      refetchNotes();
    },
  });

  const evaluateMutation = useMutation({
    mutationFn: (force: boolean) => evaluateClaim(claimId, force),
    onSuccess: (res) => {
      refetchEvals();
      refetchClaim();
      // Pre-fill approved amount from recommendation
      if (res.recommended_payout_inr) {
        setApprovedAmount(res.recommended_payout_inr.toString());
      }
    },
  });

  const decisionMutation = useMutation({
    mutationFn: () =>
      submitClaimDecision(claimId, {
        decision: decisionType,
        decision_reason: decisionReason,
        approved_amount: decisionType === "approved" ? parseFloat(approvedAmount) || undefined : undefined,
        evaluation_id: latestEvaluation?.id,
      }),
    onSuccess: (updatedClaim) => {
      setDecisionSuccessMsg(
        `Claim successfully transitioned to "${updatedClaim.status}". Decision recorded.`
      );
      refetchClaim();
      queryClient.invalidateQueries({ queryKey: ["claims"] });
      queryClient.invalidateQueries({ queryKey: ["adjuster"] });
    },
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
          href="/adjuster/queue"
          className="text-xs text-ink-muted hover:text-ink inline-flex items-center gap-1 font-medium transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" /> Back to review queue
        </Link>
      </div>

      <PageHeader
        title={`Adjuster Console: ${claim.claim_number}`}
        subtitle={`Claimant: ${claim.customer_user_id} // Policy: ${claim.policy_public_id}`}
        action={<StatusBadge status={claim.status} />}
      />

      {decisionSuccessMsg && (
        <div className="mb-6 p-4 rounded-xl bg-matcha-soft border border-matcha text-xs text-status-successText flex items-center justify-between">
          <span className="font-semibold">{decisionSuccessMsg}</span>
          <button
            onClick={() => setDecisionSuccessMsg(null)}
            className="text-status-successText font-bold underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {claim.fraud_flag && (
        <div className="mb-6 p-4 rounded-xl bg-status-dangerSoft border border-status-dangerText/30 text-xs text-status-dangerText flex items-center gap-3">
          <ShieldAlert className="w-5 h-5 shrink-0" />
          <div>
            <span className="font-bold">Fraud Review Sentinel:</span> Automated anti-fraud heuristics detected high-risk patterns. Verify claimant bills and police/medical reports before settlement approval.
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Facts & Evaluation Breakdown */}
        <div className="lg:col-span-2 space-y-6">
          {/* Claim Incident Card */}
          <div className="washi-panel p-6">
            <h3 className="font-serif font-bold text-base text-ink mb-4 pb-2 border-b border-washi-border flex items-center gap-2">
              <FileText className="w-4 h-4 text-aoi" />
              Claim Incident Facts
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs mb-4">
              <div>
                <span className="text-ink-muted block">Incident Type</span>
                <span className="font-semibold text-ink capitalize text-sm">
                  {claim.incident_type.replace(/_/g, " ")}
                </span>
              </div>
              <div>
                <span className="text-ink-muted block">Date</span>
                <span className="font-semibold text-ink text-sm">
                  {formatDate(claim.incident_date)}
                </span>
              </div>
              <div>
                <span className="text-ink-muted block">Claimed Amount</span>
                <span className="font-serif font-bold text-ink text-sm">
                  {formatINR(claim.requested_amount_inr)}
                </span>
              </div>
              <div>
                <span className="text-ink-muted block">Location</span>
                <span className="font-medium text-ink">{claim.incident_location}</span>
              </div>
            </div>
            <div className="pt-3 border-t border-washi-border">
              <span className="text-xs text-ink-muted block mb-1">Incident Circumstances</span>
              <p className="text-xs text-ink bg-surface-muted p-3 rounded-lg border border-washi-border leading-relaxed">
                {claim.incident_description}
              </p>
            </div>
          </div>

          {/* AI Evaluation Runner & Breakdown */}
          <div className="washi-panel p-6">
            <div className="flex items-center justify-between mb-4 pb-2 border-b border-washi-border">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-aoi" />
                <h3 className="font-serif font-bold text-base text-ink">
                  AI Evaluation & Rules Payout
                </h3>
              </div>
              <Button
                size="sm"
                variant="outline"
                isLoading={evaluateMutation.isPending}
                onClick={() => evaluateMutation.mutate(true)}
              >
                <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
                {latestEvaluation ? "Re-run Evaluation" : "Run Evaluation"}
              </Button>
            </div>

            {latestEvaluation ? (
              <div className="space-y-6">
                {/* Recommendation Banner */}
                <div className="p-4 rounded-xl bg-aoi-wash/50 border border-aoi/30 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-aoi">
                      AI Recommendation
                    </span>
                    <div className="text-2xl font-serif font-bold text-aoi capitalize">
                      {latestEvaluation.recommendation}
                    </div>
                  </div>
                  <div>
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-ink-muted">
                      Recommended Payout
                    </span>
                    <div className="text-2xl font-serif font-bold text-ink">
                      {formatINR(latestEvaluation.recommended_payout_inr)}
                    </div>
                  </div>
                  <div>
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-ink-muted">
                      Review Flag
                    </span>
                    <div>
                      {latestEvaluation.requires_human_review ? (
                        <span className="inline-flex items-center gap-1 text-xs font-semibold text-status-warningText bg-[#FFF4E5] px-2 py-0.5 rounded border border-[#F6D09F]">
                          <AlertTriangle className="w-3 h-3" /> Human Review Required
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-xs font-semibold text-status-successText bg-matcha-soft px-2 py-0.5 rounded border border-matcha/40">
                          <CheckCircle2 className="w-3 h-3" /> Auto-Eligible
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Calculation Breakdown */}
                {latestEvaluation.calculation_breakdown && (
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-ink mb-2 flex items-center gap-1.5">
                      <Calculator className="w-3.5 h-3.5 text-aoi" />
                      Deterministic Payout Breakdown
                    </h4>
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs mb-3">
                      <div className="p-3 rounded-lg bg-surface-muted border border-washi-border">
                        <span className="text-ink-muted block">Applicable Limit</span>
                        <span className="font-semibold text-ink">
                          {formatINR(latestEvaluation.calculation_breakdown.applicable_limit)}
                        </span>
                      </div>
                      <div className="p-3 rounded-lg bg-surface-muted border border-washi-border">
                        <span className="text-ink-muted block">Deductible</span>
                        <span className="font-semibold text-ink">
                          {formatINR(latestEvaluation.calculation_breakdown.deductible)}
                        </span>
                      </div>
                      <div className="p-3 rounded-lg bg-surface-muted border border-washi-border">
                        <span className="text-ink-muted block">Base Payout</span>
                        <span className="font-semibold text-ink">
                          {formatINR(latestEvaluation.calculation_breakdown.base_payout)}
                        </span>
                      </div>
                      <div className="p-3 rounded-lg bg-matcha-soft/50 border border-matcha/40">
                        <span className="text-status-successText block font-semibold">Final Recommended</span>
                        <span className="font-bold text-status-successText">
                          {formatINR(latestEvaluation.calculation_breakdown.final_payout)}
                        </span>
                      </div>
                    </div>

                    {/* Step explanations */}
                    {latestEvaluation.calculation_breakdown.explanation_steps && (
                      <div className="space-y-1.5">
                        {latestEvaluation.calculation_breakdown.explanation_steps.map((st, i) => (
                          <div
                            key={i}
                            className="p-2.5 rounded-lg bg-surface border border-washi-border text-[11px] flex items-center justify-between"
                          >
                            <span className="font-mono text-ink-muted">{st.step}</span>
                            <span className="font-medium text-ink">{st.note}</span>
                            {st.amount_inr !== undefined && (
                              <span className="font-mono font-semibold text-aoi">
                                {formatINR(st.amount_inr)}
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Coverage Findings & Validation Flags */}
                {latestEvaluation.coverage_findings && latestEvaluation.coverage_findings.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold uppercase tracking-wider text-ink mb-2">
                      Coverage Findings
                    </h4>
                    <ul className="list-disc pl-5 text-xs text-ink-muted space-y-1">
                      {latestEvaluation.coverage_findings.map((f, i) => (
                        <li key={i}>{f}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-xs text-ink-muted">
                No evaluation run yet for this claim. Click "Run Evaluation" above to compute policy limits and deductible rules.
              </div>
            )}
          </div>

          {/* Explicit Human Decision Workflow */}
          <div className="washi-panel p-6 border-aoi/30 bg-gradient-to-b from-surface to-surface-muted/30">
            <h3 className="font-serif font-bold text-base text-ink mb-2">
              Adjudicator Decision Action
            </h3>
            <p className="text-xs text-ink-muted mb-4">
              Commit a formal underwriting decision. Human approval is required to finalize payout authorization.
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-ink mb-1.5">
                  Decision Outcome *
                </label>
                <div className="grid grid-cols-3 gap-3 text-xs">
                  <button
                    type="button"
                    onClick={() => setDecisionType("approved")}
                    className={`p-3 rounded-lg border font-medium flex items-center justify-center gap-1.5 transition-colors ${
                      decisionType === "approved"
                        ? "bg-matcha-soft border-matcha text-status-successText shadow-xs font-bold"
                        : "bg-surface border-washi-border text-ink-muted hover:text-ink"
                    }`}
                  >
                    <CheckCircle2 className="w-4 h-4" /> Approve
                  </button>
                  <button
                    type="button"
                    onClick={() => setDecisionType("denied")}
                    className={`p-3 rounded-lg border font-medium flex items-center justify-center gap-1.5 transition-colors ${
                      decisionType === "denied"
                        ? "bg-status-dangerSoft border-status-dangerText/40 text-status-dangerText shadow-xs font-bold"
                        : "bg-surface border-washi-border text-ink-muted hover:text-ink"
                    }`}
                  >
                    <XCircle className="w-4 h-4" /> Deny
                  </button>
                  <button
                    type="button"
                    onClick={() => setDecisionType("request_information")}
                    className={`p-3 rounded-lg border font-medium flex items-center justify-center gap-1.5 transition-colors ${
                      decisionType === "request_information"
                        ? "bg-[#FFF4E5] border-[#F6D09F] text-status-warningText shadow-xs font-bold"
                        : "bg-surface border-washi-border text-ink-muted hover:text-ink"
                    }`}
                  >
                    <HelpCircle className="w-4 h-4" /> Request Info
                  </button>
                </div>
              </div>

              {decisionType === "approved" && (
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-wider text-ink mb-1">
                    Final Approved Settlement Amount (INR) *
                  </label>
                  <input
                    type="number"
                    step="any"
                    value={approvedAmount}
                    onChange={(e) => setApprovedAmount(e.target.value)}
                    placeholder="e.g. 25000"
                    className="w-full px-3.5 py-2 text-sm rounded-lg border border-washi-border bg-surface text-ink font-mono focus:ring-2 focus:ring-aoi focus:outline-none"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-ink mb-1">
                  Adjudicator Decision Reason / Clause Justification *
                </label>
                <textarea
                  rows={3}
                  value={decisionReason}
                  onChange={(e) => setDecisionReason(e.target.value)}
                  placeholder="State the policy clause, evidence verified, or reason for denial / information request..."
                  className="w-full px-3.5 py-2 text-sm rounded-lg border border-washi-border bg-surface text-ink focus:ring-2 focus:ring-aoi focus:outline-none leading-relaxed"
                />
              </div>

              <div className="pt-2 flex justify-end">
                <Button
                  variant="primary"
                  isLoading={decisionMutation.isPending}
                  disabled={!decisionReason.trim() || (decisionType === "approved" && !approvedAmount)}
                  onClick={() => decisionMutation.mutate()}
                >
                  Confirm & Commit Decision
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Append-only Adjuster Notes */}
        <div className="space-y-6">
          <div className="washi-panel p-6 flex flex-col h-[700px]">
            <h3 className="font-serif font-bold text-base text-ink mb-4 pb-2 border-b border-washi-border flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-aoi" />
              Adjuster Notes & Audit Trail
            </h3>

            {/* Notes List */}
            <div className="flex-1 overflow-y-auto space-y-3 pr-1">
              {notesLoading ? (
                <div className="space-y-2">
                  <div className="h-16 skeleton w-full" />
                  <div className="h-16 skeleton w-full" />
                </div>
              ) : !notes || notes.length === 0 ? (
                <div className="text-center py-12 text-xs text-ink-muted">
                  No internal notes recorded yet for this claim.
                </div>
              ) : (
                notes.map((note) => (
                  <div
                    key={note.id}
                    className="p-3.5 rounded-xl bg-surface-muted border border-washi-border text-xs space-y-1.5"
                  >
                    <div className="flex items-center justify-between text-[10px] text-ink-muted">
                      <span className="font-mono font-semibold text-ink">
                        {note.author_user_id}
                      </span>
                      <span>{formatDateTime(note.created_at)}</span>
                    </div>
                    <p className="text-ink leading-relaxed whitespace-pre-wrap">{note.note_text}</p>
                  </div>
                ))
              )}
            </div>

            {/* Note Composer */}
            <div className="pt-4 border-t border-washi-border mt-3">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (noteText.trim()) addNoteMutation.mutate(noteText);
                }}
                className="space-y-2"
              >
                <textarea
                  rows={3}
                  value={noteText}
                  onChange={(e) => setNoteText(e.target.value)}
                  placeholder="Add confidential adjuster observation, hospital verification, or document notes..."
                  className="w-full px-3 py-2 text-xs rounded-lg border border-washi-border bg-surface text-ink focus:ring-2 focus:ring-aoi focus:outline-none"
                />
                <Button
                  type="submit"
                  variant="secondary"
                  size="sm"
                  isLoading={addNoteMutation.isPending}
                  disabled={!noteText.trim()}
                  className="w-full"
                >
                  <Send className="w-3.5 h-3.5 mr-1.5" />
                  Append Internal Note
                </Button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
