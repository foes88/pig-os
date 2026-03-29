"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", icon: "🧠", label: "AI Dashboard" },
  { href: "/sows", icon: "🐷", label: "Sow Intelligence" },
  { href: "/record", icon: "✏️", label: "Smart Record" },
  { href: "/kpi", icon: "📊", label: "Predictive KPI" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <nav className="fixed top-0 left-0 w-[220px] h-screen bg-[#0F172A] border-r border-[#1E293B] py-5 flex flex-col z-50 overflow-y-auto">
      <div className="px-[18px] pb-5 text-[15px] font-extrabold text-white tracking-tight border-b border-white/[.08] mb-4">
        Pig<span className="text-[#5EEAD4]">OS</span> AI
        <span className="ml-1 text-[8px] font-bold bg-gradient-to-r from-purple-500 to-blue-500 text-white px-1.5 py-0.5 rounded align-top">
          AI
        </span>
      </div>

      {navItems.map((item) => {
        const isActive = pathname === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={`flex items-center gap-2.5 px-[18px] py-2 text-xs font-medium transition-all ${
              isActive
                ? "text-[#5EEAD4] font-semibold bg-[rgba(13,124,102,.15)] border-r-2 border-primary"
                : "text-[#8896A8] hover:text-[#CBD5E1] hover:bg-white/[.05]"
            }`}
          >
            <span className="w-[18px] text-center text-[13px]">{item.icon}</span>
            {item.label}
          </Link>
        );
      })}

      <div className="mt-auto px-[18px] py-4 text-[10px] text-[#4B5563] border-t border-white/[.06]">
        AI-Powered Revenue System
      </div>
    </nav>
  );
}
