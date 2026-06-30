"use client";

import { useEffect, useState } from "react";

import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";

import { notificationsApi } from "@/lib/api/endpoints/notifications";
import { authApi } from "@/lib/api/endpoints/auth";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";
import { Sidebar } from "@/components/Sidebar";
import { Topbar } from "@/components/Topbar";
import { BottomNav } from "@/components/BottomNav";
import { QuickInputDrawer } from "@/components/QuickInputDrawer";
import { AskAiDrawer } from "@/components/AskAiDrawer";
import { locales, isPlatformAdmin, type Locale } from "@/i18n/config";

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
  const role = useAuthStore((s) => s.user?.role);

  // chrome 언어를 next-intl 쿠키와 동기화. 비관리자가 ko 쿠키를 갖고 있으면 en으로 강제(한국어=관리자 전용).
  // role 미하이드레이트(undefined) 시엔 클램프 보류 — 섣불리 admin의 ko 선택을 덮어쓰지 않도록 role 확정 후에만.
  useEffect(() => {
    let l = readLocaleCookie();
    if (l === "ko" && role && !isPlatformAdmin(role)) {
      l = "en";
      document.cookie = `NEXT_LOCALE=en; path=/; max-age=31536000; SameSite=Lax`;
      try { localStorage.setItem("pigos_lang", "en"); } catch { /* ignore */ }
      router.refresh();
    }
    setLang(l);
  }, [role, router]);

  // 언어 변경: 쿠키 set(서버 next-intl) + localStorage + 새로고침(페이지 재렌더) + chrome 즉시 갱신
  const changeLang = (l: Locale) => {
    // 한국어는 플랫폼 관리자만 — 비관리자 시도는 무시(방어)
    if (l === "ko" && !isPlatformAdmin(role)) return;
    document.cookie = `NEXT_LOCALE=${l}; path=/; max-age=31536000; SameSite=Lax`;
    try { localStorage.setItem("pigos_lang", l); } catch { /* ignore */ }
    setLang(l);
    router.refresh();
  };
  const farmId = useAuthStore((s) => s.activeFarmId);
  const setUser = useAuthStore((s) => s.setUser);
  const isAuthed = useAuthStore((s) => !!s.accessToken);

  // 앱 진입 시 /me 재조회 → 역할·farm_roles·접근 농장 최신화(서버측 권한 변경 반영,
  // stale activeFarmId 보정). 로그인 시점 고정값으로 굳지 않게.
  const { data: me } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: () => authApi.me(),
    enabled: isAuthed,
    staleTime: 5 * 60 * 1000,
  });
  useEffect(() => {
    if (!me) return;
    setUser({
      id: me.id, username: me.username, email: me.email ?? "", name: me.name,
      role: me.role, system_role: me.system_role, farm_ids: me.farm_ids, farm_roles: me.farm_roles,
    });
  }, [me, setUser]);

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
