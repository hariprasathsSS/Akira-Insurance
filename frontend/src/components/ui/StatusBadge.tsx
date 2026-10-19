import React from "react";
import { CheckCircle2, Clock, AlertTriangle, XCircle, Archive, ShieldAlert } from "lucide-react";

interface StatusBadgeProps {
  status: string;
  className?: string;
  showIcon?: boolean;
}

export function StatusBadge({ status, className = "", showIcon = true }: StatusBadgeProps) {
  const norm = (status || "").toLowerCase().trim();

  let styles = "bg-surface-muted text-ink-muted border-washi-border";
  let icon = <Clock className="w-3.5 h-3.5 mr-1.5" />;
  let label = status.replace(/_/g, " ");

  if (["active", "paid", "succeeded", "indexed", "approved"].includes(norm)) {
    styles = "bg-matcha-soft text-status-successText border-[#B8C8AD]/60";
    icon = <CheckCircle2 className="w-3.5 h-3.5 mr-1.5 text-status-successText" />;
  } else if (["submitted", "evaluated", "info", "open"].includes(norm)) {
    styles = "bg-aoi-wash text-aoi border-aoi/30";
    icon = <Clock className="w-3.5 h-3.5 mr-1.5 text-aoi" />;
  } else if (["due", "overdue", "under_review", "indexing", "queued", "pending_review", "pending_approval"].includes(norm)) {
    styles = "bg-[#FFF4E5] text-status-warningText border-[#F6D09F]";
    icon = <Clock className="w-3.5 h-3.5 mr-1.5 text-status-warningText" />;
  } else if (["denied", "failed", "cancelled", "lapsed"].includes(norm)) {
    styles = "bg-status-dangerSoft text-status-dangerText border-[#F1B8BA]";
    icon = <XCircle className="w-3.5 h-3.5 mr-1.5 text-status-dangerText" />;
  } else if (["archived", "closed", "superseded"].includes(norm)) {
    styles = "bg-surface-muted text-ink-muted border-washi-border";
    icon = <Archive className="w-3.5 h-3.5 mr-1.5 text-ink-muted" />;
  } else if (norm === "fraud_suspected" || norm === "flagged") {
    styles = "bg-status-dangerSoft text-status-dangerText border-status-dangerText/40";
    icon = <ShieldAlert className="w-3.5 h-3.5 mr-1.5 text-status-dangerText" />;
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border capitalize transition-colors ${styles} ${className}`}
    >
      {showIcon && icon}
      <span>{label}</span>
    </span>
  );
}
