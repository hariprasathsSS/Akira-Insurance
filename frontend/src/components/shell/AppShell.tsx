"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { usePersonaStore } from "@/store/persona-store";
import { PersonaSwitcher } from "./PersonaSwitcher";
import {
  FileText,
  CreditCard,
  FileCheck2,
  BotMessageSquare,
  ShieldAlert,
  BarChart3,
  Layers,
  Cpu,
  PlusCircle,
  LayoutDashboard,
} from "lucide-react";

interface AppShellProps {
  children: React.ReactNode;
}

export function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const { currentUser } = usePersonaStore();
  const role = currentUser?.role || "customer";

  const customerNav = [
    { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
    { name: "My Policies", href: "/policies", icon: FileText },
    { name: "Billing", href: "/billing", icon: CreditCard },
    { name: "Claims", href: "/claims", icon: FileCheck2 },
    { name: "File Claim (FNOL)", href: "/claims/new", icon: PlusCircle },
    { name: "AI Assistant", href: "/assistant", icon: BotMessageSquare },
  ];

  const adjusterNav = [
    { name: "Review Queue", href: "/adjuster/queue", icon: ShieldAlert },
    { name: "All Claims", href: "/claims", icon: FileCheck2 },
  ];

  const adminNav = [
    { name: "Operations Metrics", href: "/admin/metrics", icon: BarChart3 },
    { name: "Policy Documents", href: "/admin/documents", icon: Layers },
    { name: "Ingestion Jobs", href: "/admin/jobs", icon: Cpu },
    { name: "Claims Directory", href: "/claims", icon: FileCheck2 },
  ];

  const currentNav =
    role === "admin" ? adminNav : role === "adjuster" ? adjusterNav : customerNav;

  return (
    <div className="min-h-screen app-background flex flex-col selection:bg-aoi-wash selection:text-ink">
      {/* Top Banner & Header */}
      <header className="sticky top-0 z-30 bg-surface/90 backdrop-blur-md border-b border-washi-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo and Brand */}
            <div className="flex items-center gap-6">
              <Link href="/dashboard" className="flex items-center gap-3 group">
                <div className="w-9 h-9 rounded-xl bg-aoi text-white flex items-center justify-center font-serif text-lg font-bold shadow-sm transition-transform group-hover:scale-105">
                  旭
                </div>
                <div>
                  <span className="font-serif font-bold text-lg tracking-tight text-ink">
                    AKIRA
                  </span>
                  <span className="text-xs uppercase tracking-widest text-ink-muted ml-1.5 font-sans">
                    Insurance
                  </span>
                </div>
              </Link>

              {/* Demo Mode Badge */}
              <span className="hidden md:inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium bg-sakura-soft text-ink-muted border border-sakura">
                <span className="w-1.5 h-1.5 rounded-full bg-status-dangerText mr-1.5 animate-pulse" />
                POC Demo Mode
              </span>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden lg:flex items-center space-x-1">
              {currentNav.map((item) => {
                const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                      isActive
                        ? "bg-aoi-wash text-aoi font-semibold shadow-xs"
                        : "text-ink-muted hover:text-ink hover:bg-surface-muted"
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </nav>

            {/* Persona Switcher */}
            <div className="flex items-center gap-3">
              <PersonaSwitcher />
            </div>
          </div>
        </div>

        {/* Mobile / Tablet Nav row */}
        <div className="lg:hidden border-t border-washi-border px-4 py-2 overflow-x-auto flex gap-2 no-scrollbar">
          {currentNav.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs whitespace-nowrap ${
                  isActive
                    ? "bg-aoi-wash text-aoi font-semibold"
                    : "text-ink-muted hover:text-ink hover:bg-surface-muted"
                }`}
              >
                <Icon className="w-3 h-3" />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-in fade-in duration-200">
        {children}
      </main>

      {/* Footer */}
      <footer className="border-t border-washi-border py-6 text-center text-xs text-ink-muted">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div>AKIRA INSURANCE AI — Enterprise Insurance Claims & Policy Operations</div>
          <div className="text-[11px] font-mono text-ink-muted">
            FastAPI 0.115 // LangGraph 0.2 // Qdrant // TanStack Query
          </div>
        </div>
      </footer>
    </div>
  );
}
