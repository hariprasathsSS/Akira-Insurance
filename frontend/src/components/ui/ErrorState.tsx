import React from "react";
import { AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "./Button";
import { ApiError } from "@/lib/api/errors";

interface ErrorStateProps {
  error: Error | ApiError | unknown;
  onRetry?: () => void;
  title?: string;
}

export function ErrorState({ error, onRetry, title = "Unable to load data" }: ErrorStateProps) {
  const isApiError = error instanceof ApiError;
  const message = error instanceof Error ? error.message : "An unexpected error occurred.";
  const code = isApiError ? error.code : undefined;
  const requestId = isApiError ? error.requestId : undefined;

  return (
    <div className="washi-panel p-8 text-center max-w-lg mx-auto my-8 border-status-dangerText/30 bg-[#FFFBFB]">
      <div className="w-12 h-12 rounded-full bg-status-dangerSoft border border-status-dangerText/20 flex items-center justify-center text-status-dangerText mx-auto mb-4">
        <AlertCircle className="w-6 h-6" />
      </div>
      <h3 className="font-serif text-lg font-semibold text-ink mb-1">{title}</h3>
      <p className="text-sm text-status-dangerText mb-4">{message}</p>

      {requestId && (
        <div className="text-[11px] font-mono text-ink-muted bg-surface-muted py-1 px-2.5 rounded-md inline-block mb-4 border border-washi-border">
          Request ID: {requestId}
        </div>
      )}

      {onRetry && (
        <div>
          <Button variant="outline" size="sm" onClick={onRetry}>
            <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
            Retry
          </Button>
        </div>
      )}
    </div>
  );
}
