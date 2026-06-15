"use client";

import { useState } from "react";

import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { notificationsApi } from "@/lib/api/endpoints/notifications";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";
import { Sidebar } from "@/components/Sidebar";
import { Topbar } from "@/components/Topbar";
import { BottomNav } from "@/components/BottomNav";
import { QuickInputDrawer } from "@/components/QuickInputDrawer";
import { AskAiDrawer } from "@/components/AskAiDrawer";
import type { Locale } from "@/i18n/config";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const [lang, setLang] = useState<Locale>("ko");
  const [collapsed, setCollapsed] = useState(false);
  const [askAiOpen, setAskAiOpen] = useState(false);
  const [quickInputOpen, setQuickInputOpen] = useState(false);
  const router = useRouter();
  const farmId = useAuthStore((s) => s.activeFarmId);
  const { data: notifUnread } = useQuery({
    queryKey: queryKeys.notifications.unread(farmId ?? ""),
    queryFn: () => notificationsApi.list({ farmId: farmId!, limit: 0 }),
    enabled: !!farmId,
    refetchInterval: 5 * 60 * 1000,
  });
  const unreadCount = notifUnread?.unread_count ?? 0;

  return (
    <>
      <Sidebar
        lang={lang}
        collapsed={collapsed}
        onCollapse={() => setCollapsed((c) => !c)}
        onAskAI={() => setAskAiOpen(true)}
      />
      <div
        className={`flex flex-col min-h-screen transition-all duration-200 ${
          collapsed ? "md:ml-16" : "md:ml-56"
        }`}
      >
        <div className="sticky top-0 z-40">
          <Topbar
            lang={lang}
            onLangToggle={setLang}
            onQuickInput={() => setQuickInputOpen(true)}
            onBell={() => router.push("/notifications")}
            alertCount={unreadCount}
          />
        </div>
        <main className="flex-1 pb-16 md:pb-0">
          {children}
        </main>
      </div>
      <BottomNav lang={lang} onAskAI={() => setAskAiOpen(true)} alertCount={unreadCount} />
      <QuickInputDrawer
        open={quickInputOpen}
        onClose={() => setQuickInputOpen(false)}
        lang={lang}
      />
      <AskAiDrawer
        open={askAiOpen}
        onClose={() => setAskAiOpen(false)}
        lang={lang}
      />
    </>
  );
}
