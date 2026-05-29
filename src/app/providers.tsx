"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { NextIntlClientProvider } from "next-intl";
import { useState, type ReactNode } from "react";
import { useUiStore } from "@/store/ui.store";

interface ProvidersProps {
  children: ReactNode;
  messages: Record<string, unknown>;
  locale: string;
}

export function Providers({ children, messages, locale }: ProvidersProps) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 60 * 1000,        // 1 min
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <NextIntlClientProvider messages={messages} locale={locale}>
        {children}
        <UpgradeModalSlot />
      </NextIntlClientProvider>
    </QueryClientProvider>
  );
}

// Stub — will be replaced with real modal component when design arrives
function UpgradeModalSlot() {
  const { upgradeModalOpen, closeUpgradeModal, upgradeModalFeature } = useUiStore();
  if (!upgradeModalOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
      <div className="bg-white rounded-2xl p-8 max-w-sm w-full mx-4 shadow-2xl">
        <h2 className="text-lg font-bold mb-2">Upgrade required</h2>
        <p className="text-sm text-gray-600 mb-4">
          {upgradeModalFeature
            ? `Feature "${upgradeModalFeature}" requires a premium plan.`
            : "This feature requires a premium plan."}
        </p>
        <div className="flex gap-3">
          <button
            onClick={closeUpgradeModal}
            className="flex-1 border border-gray-200 rounded-lg py-2 text-sm"
          >
            Later
          </button>
          <button className="flex-1 bg-blue-600 text-white rounded-lg py-2 text-sm font-medium">
            View Plans
          </button>
        </div>
      </div>
    </div>
  );
}
