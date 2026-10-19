"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { AppShell } from "@/components/shell/AppShell";
import { PageHeader } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";
import { ErrorState } from "@/components/ui/ErrorState";
import { queryKeys } from "@/lib/query-keys";
import {
  getPolicyDocumentFamilies,
  getDocumentVersions,
  uploadPolicyDocument,
  activateDocumentVersion,
  archiveDocumentVersion,
} from "@/lib/api";
import { formatDate, formatDateTime, formatBytes } from "@/lib/formatters";
import { ApiError } from "@/lib/api/errors";
import {
  Layers,
  Upload,
  CheckCircle2,
  Archive,
  AlertCircle,
  FileText,
  Clock,
  ArrowRight,
  ShieldCheck,
} from "lucide-react";

export default function AdminDocumentsPage() {
  const queryClient = useQueryClient();
  const [selectedFamilyId, setSelectedFamilyId] = useState<string | null>(null);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [uploadNotice, setUploadNotice] = useState<{ job_id: string; message: string } | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  // Queries
  const {
    data: families,
    isLoading: familiesLoading,
    error: familiesError,
    refetch: refetchFamilies,
  } = useQuery({
    queryKey: queryKeys.adminDocuments,
    queryFn: getPolicyDocumentFamilies,
  });

  const activeFamily =
    families?.find((f) => f.public_id === selectedFamilyId) || (families && families[0]) || null;

  const currentFamilyId = activeFamily?.public_id;

  const {
    data: versions,
    isLoading: versionsLoading,
    refetch: refetchVersions,
  } = useQuery({
    queryKey: queryKeys.adminDocumentVersions(currentFamilyId || ""),
    queryFn: () => getDocumentVersions(currentFamilyId!),
    enabled: !!currentFamilyId,
  });

  // Mutations
  const activateMutation = useMutation({
    mutationFn: (versionId: number) => activateDocumentVersion(versionId),
    onSuccess: () => {
      setActionError(null);
      refetchFamilies();
      refetchVersions();
    },
    onError: (err: ApiError | Error) => {
      setActionError(err.message || "Failed to activate version.");
    },
  });

  const archiveMutation = useMutation({
    mutationFn: (versionId: number) => archiveDocumentVersion(versionId),
    onSuccess: () => {
      setActionError(null);
      refetchFamilies();
      refetchVersions();
    },
    onError: (err: ApiError | Error) => {
      setActionError(err.message || "Failed to archive version.");
    },
  });

  // Upload Form State
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [policyType, setPolicyType] = useState("health");
  const [planTier, setPlanTier] = useState("standard");
  const [docTitle, setDocTitle] = useState("");
  const [docDescription, setDocDescription] = useState("");
  const [effectiveFrom, setEffectiveFrom] = useState("2026-01-01");
  const [effectiveTo, setEffectiveTo] = useState("2026-12-31");

  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!uploadFile) throw new Error("Please select a PDF file to upload.");
      const formData = new FormData();
      formData.append("file", uploadFile);
      formData.append("policy_type", policyType);
      formData.append("plan_tier", planTier);
      formData.append("title", docTitle || `${policyType.toUpperCase()} ${planTier.toUpperCase()} Policy`);
      if (docDescription) formData.append("description", docDescription);
      formData.append("effective_from", effectiveFrom);
      formData.append("effective_to", effectiveTo);
      return uploadPolicyDocument(formData);
    },
    onSuccess: (res) => {
      setUploadNotice({
        job_id: res.job_public_id,
        message: "Policy PDF accepted for background indexing (HTTP 202).",
      });
      setIsUploadOpen(false);
      setUploadFile(null);
      refetchFamilies();
      refetchVersions();
      queryClient.invalidateQueries({ queryKey: queryKeys.adminJobs() });
    },
    onError: (err: ApiError | Error) => {
      setActionError(err.message || "Upload failed.");
    },
  });

  return (
    <AppShell>
      <PageHeader
        title="Policy Document Management & Ingestion"
        subtitle="Manage master policy contract families, version activation, and RAG chunk vectorization."
        action={
          <Button variant="primary" onClick={() => setIsUploadOpen(true)}>
            <Upload className="w-4 h-4 mr-2" />
            Upload New Policy PDF
          </Button>
        }
      />

      {uploadNotice && (
        <div className="mb-6 p-4 rounded-xl bg-aoi-wash/60 border border-aoi/30 text-xs text-aoi flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4" />
            <span>
              <strong>{uploadNotice.message}</strong> Ingestion Job ID: <span className="font-mono">{uploadNotice.job_id}</span>
            </span>
          </div>
          <Link href="/admin/jobs" className="font-bold underline text-aoi-deep">
            Monitor Job Ingestion &rarr;
          </Link>
        </div>
      )}

      {actionError && (
        <div className="mb-6 p-4 rounded-xl bg-status-dangerSoft border border-status-dangerText/30 text-xs text-status-dangerText flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            <span>{actionError}</span>
          </div>
          <button onClick={() => setActionError(null)} className="font-bold underline">
            Dismiss
          </button>
        </div>
      )}

      {familiesLoading ? (
        <div className="space-y-4">
          <div className="h-16 skeleton washi-panel" />
          <div className="h-64 skeleton washi-panel" />
        </div>
      ) : familiesError ? (
        <ErrorState error={familiesError} onRetry={refetchFamilies} />
      ) : !families || !Array.isArray(families) || families.length === 0 ? (
        <EmptyState
          title="No Document Families"
          description="There are currently no policy document families registered."
          actionText="Upload Policy PDF"
          onAction={() => setIsUploadOpen(true)}
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Left Column: Family Selector */}
          <div className="washi-panel p-4 space-y-2 h-fit">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-ink-muted px-2 py-1">
              Document Families ({families.length})
            </h3>
            {families.map((fam) => {
              const isSelected = fam.public_id === activeFamily?.public_id;
              return (
                <button
                  key={fam.public_id}
                  onClick={() => setSelectedFamilyId(fam.public_id)}
                  className={`w-full text-left p-3 rounded-lg text-xs transition-colors flex items-start gap-2.5 ${
                    isSelected
                      ? "bg-aoi text-white font-medium shadow-xs"
                      : "hover:bg-surface-muted text-ink"
                  }`}
                >
                  <Layers className={`w-4 h-4 shrink-0 mt-0.5 ${isSelected ? "text-white" : "text-aoi"}`} />
                  <div className="flex-1 min-w-0">
                    <div className="truncate font-semibold">{fam.title}</div>
                    <div className={`text-[10px] uppercase font-mono ${isSelected ? "text-white/80" : "text-ink-muted"}`}>
                      {fam.policy_type} • {fam.plan_tier}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Right Column: Versions Table & Activation */}
          <div className="lg:col-span-3 space-y-6">
            {activeFamily && (
              <div className="washi-panel p-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-washi-border mb-6 gap-2">
                  <div>
                    <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-surface-muted text-ink-muted border border-washi-border">
                      Family: {activeFamily.public_id}
                    </span>
                    <h2 className="font-serif text-xl font-bold text-ink mt-1">
                      {activeFamily.title}
                    </h2>
                    <p className="text-xs text-ink-muted mt-0.5">
                      {activeFamily.description || "Official underwriting policy contract wording."}
                    </p>
                  </div>
                  <div className="text-xs text-ink-muted">
                    Active Version: <span className="font-mono font-bold text-ink">v{activeFamily.active_version_number ?? "None"}</span>
                  </div>
                </div>

                {versionsLoading ? (
                  <div className="space-y-3">
                    <div className="h-12 skeleton w-full" />
                    <div className="h-12 skeleton w-full" />
                  </div>
                ) : !versions || !Array.isArray(versions) || versions.length === 0 ? (
                  <p className="text-xs text-ink-muted text-center py-8">
                    No versions found for this family.
                  </p>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead>
                        <tr className="border-b border-washi-border bg-surface-muted text-ink-muted uppercase tracking-wider font-semibold">
                          <th className="py-2.5 px-3">Ver</th>
                          <th className="py-2.5 px-3">File / Size</th>
                          <th className="py-2.5 px-3">Status</th>
                          <th className="py-2.5 px-3">Active</th>
                          <th className="py-2.5 px-3">Uploaded</th>
                          <th className="py-2.5 px-3 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-washi-border/60">
                        {versions.map((ver) => (
                          <tr key={ver.id} className="hover:bg-surface-muted/50 transition-colors">
                            <td className="py-3 px-3 font-mono font-bold text-ink">
                              v{ver.version_number}
                            </td>
                            <td className="py-3 px-3">
                              <div className="font-medium text-ink flex items-center gap-1.5">
                                <FileText className="w-3.5 h-3.5 text-aoi" />
                                {ver.file_name}
                              </div>
                              <div className="text-[10px] text-ink-muted font-mono">
                                {formatBytes(ver.file_size_bytes)}
                              </div>
                            </td>
                            <td className="py-3 px-3">
                              <StatusBadge status={ver.status} />
                            </td>
                            <td className="py-3 px-3">
                              {ver.is_active ? (
                                <span className="inline-flex items-center gap-1 text-[11px] font-bold text-status-successText bg-matcha-soft px-2 py-0.5 rounded-full border border-matcha/40">
                                  <CheckCircle2 className="w-3 h-3" /> Active
                                </span>
                              ) : (
                                <span className="text-ink-muted text-[11px]">Inactive</span>
                              )}
                            </td>
                            <td className="py-3 px-3 text-ink-muted">
                              {formatDateTime(ver.created_at)}
                            </td>
                            <td className="py-3 px-3 text-right space-x-2">
                              {!ver.is_active && ver.status === "indexed" && (
                                <Button
                                  size="sm"
                                  variant="primary"
                                  isLoading={activateMutation.isPending}
                                  onClick={() => activateMutation.mutate(ver.id)}
                                >
                                  Activate
                                </Button>
                              )}
                              {ver.status !== "archived" && !ver.is_active && (
                                <Button
                                  size="sm"
                                  variant="secondary"
                                  isLoading={archiveMutation.isPending}
                                  onClick={() => archiveMutation.mutate(ver.id)}
                                >
                                  <Archive className="w-3 h-3 mr-1" />
                                  Archive
                                </Button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Upload Modal */}
      {isUploadOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink/40 backdrop-blur-xs">
          <div className="washi-panel p-6 sm:p-8 max-w-lg w-full bg-surface shadow-dialog animate-in fade-in zoom-in-95">
            <h3 className="font-serif text-lg font-bold text-ink mb-1">
              Upload Policy Document (PDF)
            </h3>
            <p className="text-xs text-ink-muted mb-6">
              PDF contracts are chunked, vectorized with sentence-transformers/BGE-M3, and stored in Qdrant for RAG.
            </p>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                uploadMutation.mutate();
              }}
              className="space-y-4 text-xs"
            >
              <div>
                <label className="block font-semibold uppercase tracking-wider text-ink mb-1">
                  PDF Document File *
                </label>
                <input
                  type="file"
                  accept="application/pdf"
                  required
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="w-full text-xs text-ink file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-aoi-wash file:text-aoi hover:file:bg-aoi hover:file:text-white transition-all cursor-pointer"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block font-semibold uppercase tracking-wider text-ink mb-1">
                    Policy Type *
                  </label>
                  <select
                    value={policyType}
                    onChange={(e) => setPolicyType(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-washi-border bg-surface text-ink capitalize focus:ring-2 focus:ring-aoi focus:outline-none"
                  >
                    <option value="health">Health Insurance</option>
                    <option value="motor">Motor Vehicle</option>
                    <option value="property">Home & Property</option>
                  </select>
                </div>
                <div>
                  <label className="block font-semibold uppercase tracking-wider text-ink mb-1">
                    Plan Tier *
                  </label>
                  <select
                    value={planTier}
                    onChange={(e) => setPlanTier(e.target.value)}
                    className="w-full px-3 py-2 rounded-lg border border-washi-border bg-surface text-ink capitalize focus:ring-2 focus:ring-aoi focus:outline-none"
                  >
                    <option value="basic">Basic</option>
                    <option value="standard">Standard</option>
                    <option value="premium">Premium</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-semibold uppercase tracking-wider text-ink mb-1">
                  Policy Title
                </label>
                <input
                  type="text"
                  placeholder="e.g. Health Guard Gold Comprehensive Policy"
                  value={docTitle}
                  onChange={(e) => setDocTitle(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-washi-border bg-surface text-ink focus:ring-2 focus:ring-aoi focus:outline-none"
                />
              </div>

              <div>
                <label className="block font-semibold uppercase tracking-wider text-ink mb-1">
                  Description / Wording Notes
                </label>
                <textarea
                  rows={2}
                  placeholder="Summary of terms or revision notes..."
                  value={docDescription}
                  onChange={(e) => setDocDescription(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-washi-border bg-surface text-ink focus:ring-2 focus:ring-aoi focus:outline-none"
                />
              </div>

              <div className="pt-4 border-t border-washi-border flex items-center justify-end gap-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsUploadOpen(false)}
                  disabled={uploadMutation.isPending}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  isLoading={uploadMutation.isPending}
                  disabled={!uploadFile}
                >
                  Upload & Vectorize
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AppShell>
  );
}
