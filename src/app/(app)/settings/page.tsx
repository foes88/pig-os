"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  User,
  CreditCard,
  Globe,
  Bell,
  Building2,
  Sliders,
  Target,
  FileText,
  LifeBuoy,
  Megaphone,
  LogOut,
  Trash2,
  ChevronRight,
  type LucideIcon,
} from "lucide-react";
import { useAuthStore } from "@/store/auth.store";

interface SettingItem {
  icon: LucideIcon;
  label: string;
  desc?: string;
  href?: string;
  onClick?: () => void;
  danger?: boolean;
}

export default function SettingsPage() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const clearAuth = useAuthStore((s) => s.clearAuth);

  const handleLogout = () => {
    clearAuth();
    document.cookie = "pigos_session=; path=/; max-age=0";
    router.replace("/login");
  };

  const sections: { title: string; items: SettingItem[] }[] = [
    {
      title: "계정",
      items: [
        { icon: User,       label: "프로필",      desc: "이름, 연락처 편집",          href: "/settings/profile" },
        { icon: Globe,      label: "언어",        desc: "한국어",                      href: "/settings/profile" },
        { icon: Bell,       label: "알림 설정",   desc: "알림 수신 채널 관리",         href: "/notifications" },
      ],
    },
    {
      title: "농장",
      items: [
        { icon: Building2,  label: "농장 정보",   desc: "농장명, 국가, 모돈 규모",     href: "/settings/profile" },
        { icon: Sliders,    label: "번식 설정",   desc: "임신/포유/WSI/출하 기준일",   href: "/settings/farm" },
        { icon: Target,     label: "벤치마크",    desc: "국가별 KPI 목표값",           href: "/settings/benchmarks" },
        { icon: CreditCard, label: "구독 및 결제", desc: "현재 플랜: Free",            href: "/settings/billing" },
      ],
    },
    {
      title: "지원",
      items: [
        { icon: Megaphone,  label: "공지사항",    href: "/announcements" },
        { icon: LifeBuoy,   label: "고객 지원",   href: "/support" },
        { icon: FileText,   label: "약관 및 정책", href: "/legal" },
      ],
    },
    {
      title: "기타",
      items: [
        { icon: LogOut, label: "로그아웃", onClick: handleLogout },
        { icon: Trash2, label: "계정 삭제", desc: "모든 데이터가 영구 삭제됩니다", href: "/settings/delete-account", danger: true },
      ],
    },
  ];

  return (
    <div className="max-w-2xl mx-auto px-7 py-6">
      <h1 className="text-xl font-extrabold tracking-tight text-text mb-1">설정</h1>
      <p className="text-[13px] text-text3 mb-6">계정과 농장 환경을 관리합니다</p>

      {/* User card */}
      {user && (
        <div className="flex items-center gap-3.5 bg-surface border border-border rounded-2xl px-5 py-4 mb-6">
          <div className="w-11 h-11 rounded-full bg-purple flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
            {user.name.slice(0, 2).toUpperCase()}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm font-bold text-text truncate">{user.name}</div>
            <div className="text-xs text-text3 truncate">{user.email}</div>
          </div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-primary bg-primary/8 border border-primary/20 rounded-full px-2.5 py-1">
            {user.role}
          </span>
        </div>
      )}

      {/* Sections */}
      <div className="space-y-6">
        {sections.map((section) => (
          <div key={section.title}>
            <div className="px-1 pb-2 text-[11px] font-bold text-text3 uppercase tracking-widest">
              {section.title}
            </div>
            <div className="bg-surface border border-border rounded-2xl overflow-hidden divide-y divide-border">
              {section.items.map((item) => {
                const Icon = item.icon;
                const inner = (
                  <>
                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                      item.danger ? "bg-red-50" : "bg-bg2"
                    }`}>
                      <Icon size={15} className={item.danger ? "text-red-500" : "text-text2"} strokeWidth={1.8} />
                    </div>
                    <div className="flex-1 min-w-0 text-left">
                      <div className={`text-[13px] font-semibold ${item.danger ? "text-red-500" : "text-text"}`}>
                        {item.label}
                      </div>
                      {item.desc && <div className="text-[11px] text-text3 mt-0.5">{item.desc}</div>}
                    </div>
                    <ChevronRight size={14} className="text-text3/50 flex-shrink-0" />
                  </>
                );
                const cls = "w-full flex items-center gap-3 px-4 py-3 hover:bg-bg2/60 transition";
                return item.href ? (
                  <Link key={item.label} href={item.href} className={cls}>{inner}</Link>
                ) : (
                  <button key={item.label} onClick={item.onClick} className={cls}>{inner}</button>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      <p className="text-center text-[11px] text-text3/60 mt-8">PigOS v0.1.0 · © 2026 WiseLake Inc.</p>
    </div>
  );
}
