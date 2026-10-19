"use client";

import React, { useEffect, useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { usePersonaStore } from "@/store/persona-store";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 1000 * 30, // 30 seconds
            refetchOnWindowFocus: false,
            retry: 1,
          },
        },
      })
  );

  const currentPersonaId = usePersonaStore((state) => state.currentPersonaId);

  // Invalidate and clear user-scoped cache immediately upon persona change
  useEffect(() => {
    queryClient.cancelQueries();
    queryClient.clear();
  }, [currentPersonaId, queryClient]);

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
