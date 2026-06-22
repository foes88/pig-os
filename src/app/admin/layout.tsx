"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { ShieldCheck, ArrowLeft } from "lucide-react";
import { useAuthStore } from "@/store/auth.store";
import { isPlatformAdmin } from "@/i18n/config";
import { ADMIN_NAV } from "@/lib/admin/nav";

// 운영자 어드민 셸 — SUPER_ADMIN 전용. 고객 앱 셸((app))과 분리된 자체 chrome.
// 게이트: ①클라이언트(이 레이아웃) ②백엔드 require_super_admin(403). 도메인은 admin.pigos.io로 분기 가능.
export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const t = useTranslations("admin");
  const user = useAuthStore((s) => s.user);
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  useEffect(() => {
    if (!mounted) return;
    if (!user) router.replace("/login");
    else if (!isPlatformAdmin(user.role)) router.replace("/");
  }, [mounted, user, router]);

  // 하이드레이트 전/비인가 시 콘텐츠 노출 금지
  if (!mounted || !user || !isPlatformAdmin(user.role)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-bg">
        <p className="text-text3 text-sm">{t("checkingAccess")}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex bg-bg">
      {/* Admin sidebar (dark console) */}
      <aside className="w-56 shrink-0 bg-console text-white flex flex-col">
        <div className="h-14 flex items-center gap-2 px-4 border-b border-white/10">
          <ShieldCheck size={18} className="text-primary" />
          <span className="font-extrabold tracking-tight">PigOS <span className="text-primary">Admin</span></span>
        </div>
        <nav className="flex-1 py-3">
          {ADMIN_NAV.map(({ href, labelKey, icon: Icon, status }) => {
            const active = href === "/admin" ? pathname === href : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-2.5 px-4 py-2.5 text-sm font-medium transition border-l-[3px] ${
                  active ? "border-primary bg-white/10 text-white" : "border-transparent text-white/70 hover:text-white hover:bg-white/5"
                }`}
              >
                <Icon size={16} /> <span className="flex-1">{t(labelKey)}</span>
                {status === "soon" && <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-white/10 text-white/50">{t("soon")}</span>}
              </Link>
            );
          })}
        </nav>
        <div className="p-3 border-t border-white/10">
          <div className="text-[11px] text-white/60 mb-2 truncate">{user.name} · {user.role}</div>
          <Link href="/" className="flex items-center gap-1.5 text-xs text-white/70 hover:text-white">
            <ArrowLeft size={13} /> {t("backToApp")}
          </Link>
        </div>
      </aside>

      <main className="flex-1 min-w-0">{children}</main>
    </div>
  );
}
