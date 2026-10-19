import React from "react";

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}

export function PageHeader({ title, subtitle, action }: PageHeaderProps) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8 pb-4 border-b border-washi-border">
      <div>
        <h1 className="text-2xl sm:text-3xl font-serif font-bold text-ink tracking-tight">
          {title}
        </h1>
        {subtitle && (
          <p className="mt-1 text-sm text-ink-muted font-sans leading-relaxed">
            {subtitle}
          </p>
        )}
      </div>
      {action && <div className="flex items-center gap-3 shrink-0">{action}</div>}
    </div>
  );
}
