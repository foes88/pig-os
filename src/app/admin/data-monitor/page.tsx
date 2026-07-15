"use client";

import { useQuery } from "@tanstack/react-query";
import { useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { Activity, AlertTriangle, CircleDashed, PauseCircle, CheckCircle2 } from "lucide-react";
import { adminApi } from "@/lib/api/endpoints/admin";
import type { DataMonitorRow } from "@/types/api.types";

// 운영자 — 농장별 데이터 입력 현황(Farm Data Monitor).
// 자족적 다국어(admin 콘솔은 운영자용 — 새 메시지 키 없이 인라인 7개어).
const STATUS_META: Record<DataMonitorRow["status"], { cls: string; icon: typeof Activity }> = {
  active: { cls: "bg-green-soft text-success border-success/30", icon: CheckCircle2 },
  idle: { cls: "bg-amber-soft text-warning border-warning/40", icon: PauseCircle },
  stale: { cls: "bg-red-soft text-danger border-danger/40", icon: AlertTriangle },
  onboarding: { cls: "bg-primary-soft text-primary border-primary/30", icon: CircleDashed },
};

export default function DataMonitorPage() {
  const t = useTranslations("adminDataMonitor");
  const router = useRouter();
  const { data = [], isLoading, isError } = useQuery({
    queryKey: ["admin", "data-monitor"],
    queryFn: () => adminApi.dataMonitor(),
    refetchInterval: 5 * 60 * 1000,
  });

  const counts = (["onboarding", "active", "idle", "stale"] as const).map((s) => ({
    s, n: data.filter((r) => r.status === s).length,
  }));

  return (
    <div className="p-7 max-w-6xl">
      <header className="mb-5 flex items-center gap-2.5">
        <Activity size={22} className="text-primary" />
        <div>
          <h1 className="text-[22px] font-extrabold tracking-tight">{t("title")}</h1>
          <p className="text-xs text-text3 mt-0.5">{t("sub")}</p>
        </div>
      </header>

      {/* 상태별 요약 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
        {counts.map(({ s, n }) => {
          const m = STATUS_META[s];
          return (
            <div key={s} className="bg-surface border border-border rounded-2xl p-4">
              <div className="flex items-center gap-1.5 mb-1.5">
                <m.icon size={14} className={m.cls.split(" ")[1]} />
                <span className="text-[11px] font-bold uppercase tracking-wide text-text3">{t(s)}</span>
              </div>
              <div className="text-2xl font-extrabold font-mono">{isLoading ? "—" : n}</div>
            </div>
          );
        })}
      </div>

      {isError ? (
        <div className="bg-red-soft border border-danger/30 rounded-xl p-4 text-sm text-danger">Failed to load.</div>
      ) : (
        <div className="bg-surface border border-border rounded-2xl overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm min-w-[680px]">
              <thead>
                <tr className="bg-bg2 text-text3 text-[11px] uppercase tracking-wide">
                  <th className="text-left px-4 py-2.5 font-bold">{t("farm")}</th>
                  <th className="text-left px-4 py-2.5 font-bold">{t("country")}</th>
                  <th className="text-right px-4 py-2.5 font-bold">{t("sows")}</th>
                  <th className="text-left px-4 py-2.5 font-bold">{t("last")}</th>
                  <th className="text-right px-4 py-2.5 font-bold">{t("e7")}</th>
                  <th className="text-right px-4 py-2.5 font-bold">{t("e30")}</th>
                  <th className="text-right px-4 py-2.5 font-bold">{t("issues") ?? "Issues"}</th>
                  <th className="text-left px-4 py-2.5 font-bold">{t("status")}</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr><td colSpan={8} className="px-4 py-10 text-center text-text3">…</td></tr>
                ) : data.length === 0 ? (
                  <tr><td colSpan={8} className="px-4 py-10 text-center text-text3">{t("empty")}</td></tr>
                ) : data.map((r) => {
                  const m = STATUS_META[r.status];
                  return (
                    <tr
                      key={r.farm_id}
                      onClick={() => router.push(`/admin/data-monitor/${r.farm_id}`)}
                      className="border-t border-border hover:bg-primary-soft/40 cursor-pointer"
                    >
                      <td className="px-4 py-2.5 font-semibold text-text underline decoration-dotted decoration-text3 underline-offset-2">{r.farm_name}</td>
                      <td className="px-4 py-2.5 text-text2 font-mono text-xs">{r.country}</td>
                      <td className="px-4 py-2.5 text-right font-mono">{r.sows}</td>
                      <td className="px-4 py-2.5 text-text3 font-mono text-xs">
                        {r.last_event_at ? r.last_event_at.slice(0, 10) : t("never")}
                      </td>
                      <td className="px-4 py-2.5 text-right font-mono">{r.events_7d}</td>
                      <td className="px-4 py-2.5 text-right font-mono">{r.events_30d}</td>
                      <td className="px-4 py-2.5 text-right">
                        {r.issues > 0 ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold border bg-red-soft text-danger border-danger/40">
                            <AlertTriangle size={11} />{r.issues}
                          </span>
                        ) : (
                          <span className="text-text3 font-mono text-xs">0</span>
                        )}
                      </td>
                      <td className="px-4 py-2.5">
                        <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold border ${m.cls}`}>
                          <m.icon size={11} />{t(r.status)}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
