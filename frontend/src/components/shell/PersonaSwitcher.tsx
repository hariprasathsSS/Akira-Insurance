"use client";

import React, { useState } from "react";
import { usePersonaStore, PRESET_DEMO_USERS, DemoUser } from "@/store/persona-store";
import { UserCheck, ChevronDown, Shield, User, Sparkles } from "lucide-react";

export function PersonaSwitcher() {
  const [isOpen, setIsOpen] = useState(false);
  const { currentPersonaId, currentUser, setPersona } = usePersonaStore();

  const handleSelect = (user: DemoUser) => {
    setPersona(user);
    setIsOpen(false);
  };

  return (
    <div className="relative inline-block text-left">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border border-washi-border bg-surface hover:bg-surface-muted transition-colors text-sm shadow-sm"
        aria-expanded={isOpen}
      >
        <span className="flex items-center justify-center w-6 h-6 rounded-full bg-aoi-wash text-aoi font-medium text-xs">
          {currentUser?.role === "admin" ? (
            <Shield className="w-3.5 h-3.5" />
          ) : currentUser?.role === "adjuster" ? (
            <Sparkles className="w-3.5 h-3.5" />
          ) : (
            <User className="w-3.5 h-3.5" />
          )}
        </span>
        <div className="text-left hidden sm:block">
          <div className="text-xs font-semibold text-ink leading-tight">{currentUser?.name}</div>
          <div className="text-[10px] text-ink-muted capitalize leading-none">{currentUser?.role} ({currentPersonaId})</div>
        </div>
        <ChevronDown className="w-3.5 h-3.5 text-ink-muted ml-1" />
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div className="absolute right-0 mt-2 w-72 rounded-xl bg-surface border border-washi-border shadow-dialog z-50 p-2 animate-in fade-in zoom-in-95 duration-100">
            <div className="px-3 py-2 border-b border-washi-border mb-1">
              <p className="text-xs font-medium text-ink-muted uppercase tracking-wider">Switch Persona</p>
              <p className="text-[11px] text-ink-muted">Simulate role-specific policies, claims, and actions.</p>
            </div>
            <div className="max-h-80 overflow-y-auto space-y-1">
              {PRESET_DEMO_USERS.map((user) => {
                const isSelected = user.id === currentPersonaId;
                return (
                  <button
                    key={user.id}
                    onClick={() => handleSelect(user)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm flex items-start gap-2.5 transition-colors ${
                      isSelected
                        ? "bg-aoi-wash text-aoi font-medium"
                        : "hover:bg-surface-muted text-ink"
                    }`}
                  >
                    <div className="mt-0.5">
                      {isSelected ? (
                        <UserCheck className="w-4 h-4 text-aoi" />
                      ) : (
                        <div className="w-4 h-4 rounded-full border border-washi-border" />
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-xs">{user.name}</span>
                        <span className="text-[10px] px-1.5 py-0.2 rounded bg-surface-muted uppercase font-mono text-ink-muted">
                          {user.role}
                        </span>
                      </div>
                      <div className="text-[11px] text-ink-muted line-clamp-1">{user.description}</div>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
