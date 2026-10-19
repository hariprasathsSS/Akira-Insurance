"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { usePersonaStore } from "@/store/persona-store";

export default function RootPage() {
  const router = useRouter();
  const { currentUser } = usePersonaStore();

  useEffect(() => {
    if (currentUser?.role === "admin") {
      router.replace("/admin/metrics");
    } else if (currentUser?.role === "adjuster") {
      router.replace("/adjuster/queue");
    } else {
      router.replace("/dashboard");
    }
  }, [currentUser, router]);

  return (
    <div className="min-h-screen app-background flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-aoi border-t-transparent rounded-full animate-spin" />
    </div>
  );
}
