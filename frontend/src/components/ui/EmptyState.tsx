import React from "react";
import { Inbox } from "lucide-react";
import { Button } from "./Button";

interface EmptyStateProps {
  title: string;
  description: string;
  actionText?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

export function EmptyState({
  title,
  description,
  actionText,
  onAction,
  icon,
}: EmptyStateProps) {
  return (
    <div className="washi-panel p-10 text-center flex flex-col items-center justify-center max-w-lg mx-auto my-8">
      <div className="w-12 h-12 rounded-full bg-surface-muted border border-washi-border flex items-center justify-center text-ink-muted mb-4 shadow-xs">
        {icon || <Inbox className="w-6 h-6 text-ink-muted" />}
      </div>
      <h3 className="font-serif text-lg font-semibold text-ink mb-1">{title}</h3>
      <p className="text-sm text-ink-muted mb-6 max-w-sm leading-relaxed">{description}</p>
      {actionText && onAction && (
        <Button variant="primary" onClick={onAction}>
          {actionText}
        </Button>
      )}
    </div>
  );
}
