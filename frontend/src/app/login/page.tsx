"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { usePersonaStore, PRESET_DEMO_USERS, DemoUser } from "@/store/persona-store";
import { getDemoUsers, demoLogin } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Shield, Sparkles, User, ArrowRight, CheckCircle2 } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { currentPersonaId, setPersona } = usePersonaStore();
  const [selectedUser, setSelectedUser] = useState<DemoUser>(
    PRESET_DEMO_USERS.find((u) => u.id === currentPersonaId) || PRESET_DEMO_USERS[0]
  );
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const { data: serverUsers } = useQuery({
    queryKey: ["auth", "demo-users"],
    queryFn: getDemoUsers,
  });

  const availableUsers = (serverUsers && serverUsers.length > 0 ? serverUsers : PRESET_DEMO_USERS) as DemoUser[];

  const handleLogin = async () => {
    setIsLoggingIn(true);
    try {
      await demoLogin(selectedUser.id);
      setPersona(selectedUser);

      // Route by server-validated role
      if (selectedUser.role === "admin") {
        router.push("/admin/metrics");
      } else if (selectedUser.role === "adjuster") {
        router.push("/adjuster/queue");
      } else {
        router.push("/dashboard");
      }
    } catch {
      // Fallback local selection if backend offline
      setPersona(selectedUser);
      router.push("/dashboard");
    } finally {
      setIsLoggingIn(false);
    }
  };

  return (
    <div className="min-h-screen app-background flex flex-col justify-center items-center p-4 selection:bg-aoi-wash selection:text-ink">
      <div className="washi-panel p-8 sm:p-10 max-w-lg w-full shadow-dialog border-washi-border">
        {/* Brand Crest */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-aoi text-white flex items-center justify-center font-serif text-2xl font-bold shadow-sm mx-auto mb-3">
            旭
          </div>
          <h1 className="font-serif text-2xl sm:text-3xl font-bold text-ink tracking-tight">
            AKIRA INSURANCE
          </h1>
          <p className="text-xs uppercase tracking-widest text-ink-muted mt-1 font-sans">
            AI-Driven Claims & Underwriting Adjudication
          </p>
          <div className="mt-3 inline-block px-3 py-1 rounded-full text-[11px] font-medium bg-sakura-soft text-ink-muted border border-sakura">
            Interactive POC Demo Persona Portal
          </div>
        </div>

        {/* Persona Select List */}
        <div className="space-y-3 mb-6">
          <p className="text-xs font-semibold uppercase tracking-wider text-ink-muted">
            Select a Demo Persona to Sign In:
          </p>
          <div className="max-h-72 overflow-y-auto space-y-2 pr-1">
            {availableUsers.map((user) => {
              const isSelected = selectedUser.id === user.id;
              return (
                <button
                  key={user.id}
                  type="button"
                  onClick={() => setSelectedUser(user)}
                  className={`w-full text-left p-3.5 rounded-xl border transition-all flex items-start gap-3 ${
                    isSelected
                      ? "bg-aoi-wash border-aoi/50 shadow-xs ring-2 ring-aoi/20"
                      : "bg-surface hover:bg-surface-muted border-washi-border"
                  }`}
                >
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${
                      isSelected
                        ? "bg-aoi text-white"
                        : "bg-surface-muted text-ink-muted border border-washi-border"
                    }`}
                  >
                    {user.role === "admin" ? (
                      <Shield className="w-4 h-4" />
                    ) : user.role === "adjuster" ? (
                      <Sparkles className="w-4 h-4" />
                    ) : (
                      <User className="w-4 h-4" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-xs text-ink">{user.name}</span>
                      <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-surface-muted text-ink-muted">
                        {user.role} ({user.id})
                      </span>
                    </div>
                    <div className="text-[11px] text-ink-muted truncate mt-0.5">{user.email}</div>
                    {user.description && (
                      <div className="text-[11px] text-ink-muted line-clamp-1 mt-0.5">
                        {user.description}
                      </div>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Submit */}
        <Button
          variant="primary"
          size="lg"
          className="w-full"
          isLoading={isLoggingIn}
          onClick={handleLogin}
        >
          Enter as {selectedUser.name} ({selectedUser.role})
          <ArrowRight className="w-4 h-4 ml-2" />
        </Button>
      </div>
    </div>
  );
}
