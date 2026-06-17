"use client";

import { useEffect, useState } from "react";

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
import { locales, type Locale } from "@/i18n/config";

function readLocaleCookie(): Locale {
  if (typeof document === "undefined") return "en";
  const m = document.cookie.match(/(?:^|;\s*)NEXT_LOCALE=([^;]+)/);
  const v = m?.[1] as Locale | undefined;
  return v && locales.includes(v) ? v : "en";
}

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const [lang, setLang] = useState<Locale>("en");
  const [collapsed, setCollapsed] = useState(false);
  const [askAiOpen, setAskAiOpen] = useState(false);
  const [quickInputOpen, setQuickInputOpen] = useState(false);
  const router = useRouter();

  // chrome 언어를 next-intl 쿠키와 동기화 (메뉴=내용 언어 일치)
  useEffect(() => {
    setLang(readLocaleCookie());
  }, []);

  // 언어 변경: 쿠키 set(서버 next-intl) + localStorage + 새로고침(페이지 재렌더) + chrome 즉시 갱신
  const changeLang = (l: Locale) => {
    document.cookie = `NEXT_LOCALE=${l}; path=/; max-age=31536000; SameSite=Lax`;
    try { localStorage.setItem("pigos_lang", l); } catch { /* ignore */ }
    setLang(l);
    router.refresh();
  };
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
            onLangToggle={changeLang}
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
