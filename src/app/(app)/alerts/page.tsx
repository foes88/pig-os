"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, ArrowRight } from "lucide-react";
import { alertsApi } from "@/lib/api/endpoints/alerts";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";
import type { OverdueSow, OverdueType } from "@/types/api.types";

// 6 overdue types → Korean label + recommended action route
const OVERDUE_META: Record<
  OverdueType,
  { label: string; action: "mating" | "weaning"; actionLabel: string }
> = {
  gilt_no_estrus:             { label: "후보돈 발정 미확인",   action: "mating",  actionLabel: "교배 입력" },
  gilt_overdue_mating:        { label: "후보돈 교배 지연",     action: "mating",  actionLabel: "교배 입력" },
  pregnant_overdue_farrowing: { label: "분만 예정일 초과",     action: "mating",  actionLabel: "임신 확인" },
  lactating_overdue_weaning:  { label: "이유 지연",           action: "weaning", actionLabel: "이유 입력" },
  open_overdue_mating:        { label: "공태 재교배 지연",     action: "mating",  actionLabel: "교배 입력" },
  accident_overdue_mating:    { label: "사고 후 재교배 지연",  action: "mating",  actionLabel: "교배 입력" },
};

const CULL_REASON_LABELS: Record<string, string> = {
  repeat_rts: "연속 번식사고 (3회+)",
  aged_low_performer: "고산차 저성적 (산차>7, 이유<9)",
  overdue_gilt: "장기 미교배 후보돈 (300일+)",
};

const STATUS_LABELS: Record<string, string> = {
  GILT: "후보돈",
  OPEN: "공태",
  PREGNANT: "임신",
  LACTATING: "포유",
  ACCIDENT: "사고",
};

function actionHref(row: OverdueSow): string {
  const meta = OVERDUE_META[row.type];
  return `/record?tab=${meta.action}&sowId=${row.sow_id}`;
}

export default function AlertsPage() {
  const farmId = useAuthStore((s) => s.activeFarmId);

  const { data: overdue, isLoading: loadingOverdue } = useQuery({
    queryKey: queryKeys.alerts.overdue(farmId ?? ""),
    queryFn: () => alertsApi.overdue(farmId!),
    enabled: !!farmId,
  });

  const { data: cullCandidates, isLoading: loadingCull } = useQuery({
    queryKey: queryKeys.alerts.cullCandidates(farmId ?? ""),
    queryFn: () => alertsApi.cullCandidates(farmId!),
    enabled: !!farmId,
  });

  if (!farmId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-text3">농장을 선택해주세요.</p>
      </div>
    );
  }

  const items = overdue?.items ?? [];
  const counts = overdue?.counts ?? {};
  const culls = cullCandidates ?? [];

  return (
    <div className="p-7 max-w-5xl">
      <div className="mb-6 flex items-center gap-2">
        <AlertTriangle className="w-5 h-5 text-warning" />
        <div>
          <h1 className="text-[22px] font-extrabold tracking-tight">관리 알림</h1>
          <p className="text-xs text-text3 mt-0.5">번식 주기 기준 과기한 모돈 + 도태 권고</p>
        </div>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-7">
        {(Object.keys(OVERDUE_META) as OverdueType[]).map((t) => (
          <div key={t} className="border border-border rounded-2xl px-4 py-3 bg-surface">
            <div className="text-[11px] text-text3 leading-tight mb-1">{OVERDUE_META[t].label}</div>
            <div className="text-2xl font-extrabold font-mono tabular-nums">
              {counts[t] ?? 0}
            </div>
          </div>
        ))}
        <div className="border border-red-200 rounded-2xl px-4 py-3 bg-red-50 col-span-2 md:col-span-1">
          <div className="text-[11px] text-danger leading-tight mb-1">도태 권고</div>
          <div className="text-2xl font-extrabold font-mono tabular-nums text-danger">
            {culls.length}
          </div>
        </div>
      </div>

      {/* Overdue table */}
      <section className="mb-8">
        <div className="text-[11px] font-bold text-faint uppercase tracking-widest mb-2">
          관리 대상 모돈 ({overdue?.total ?? 0})
        </div>
        {loadingOverdue ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-12 bg-border rounded-xl animate-pulse" />
            ))}
          </div>
        ) : items.length === 0 ? (
          <div className="border border-border rounded-2xl py-12 text-center text-text3">
            <p className="font-semibold">관리 대상 모돈이 없습니다</p>
            <p className="text-xs mt-1">모든 모돈이 일정 내에 있습니다.</p>
          </div>
        ) : (
          <div className="border border-border rounded-2xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-bg2 text-text3 text-[11px] uppercase tracking-wide">
                  <th className="text-left font-semibold px-4 py-2.5">유형</th>
                  <th className="text-left font-semibold px-4 py-2.5">귀표</th>
                  <th className="text-left font-semibold px-4 py-2.5">상태</th>
                  <th className="text-right font-semibold px-4 py-2.5">경과일</th>
                  <th className="text-right font-semibold px-4 py-2.5">조치</th>
                </tr>
              </thead>
              <tbody>
                {items.map((row) => (
                  <tr key={`${row.type}-${row.sow_id}`} className="border-t border-border">
                    <td className="px-4 py-2.5">{OVERDUE_META[row.type].label}</td>
                    <td className="px-4 py-2.5 font-mono font-semibold">{row.ear_tag}</td>
                    <td className="px-4 py-2.5 text-text3">{STATUS_LABELS[row.status] ?? row.status}</td>
                    <td className="px-4 py-2.5 text-right font-mono tabular-nums text-warning font-semibold">
                      +{row.overdue_days}일
                    </td>
                    <td className="px-4 py-2.5 text-right">
                      <Link
                        href={actionHref(row)}
                        className="inline-flex items-center gap-1 text-primary text-xs font-semibold hover:underline"
                      >
                        {OVERDUE_META[row.type].actionLabel}
                        <ArrowRight className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {/* Cull recommendations */}
      <section>
        <div className="text-[11px] font-bold text-faint uppercase tracking-widest mb-2">
          도태 권고 ({culls.length})
        </div>
        {loadingCull ? (
          <div className="h-12 bg-border rounded-xl animate-pulse" />
        ) : culls.length === 0 ? (
          <div className="border border-border rounded-2xl py-10 text-center text-text3">
            <p className="text-sm">도태 권고 대상이 없습니다.</p>
          </div>
        ) : (
          <div className="space-y-2">
            {culls.map((c) => (
              <div
                key={c.sow_id}
                className="border border-border rounded-2xl px-4 py-3 flex items-center justify-between gap-3"
              >
                <div className="min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-mono font-semibold text-sm">{c.ear_tag}</span>
                    <span className="text-[11px] text-text3">
                      {STATUS_LABELS[c.status] ?? c.status} · 산차 {c.parity}
                      {c.last_weaned != null && ` · 최근이유 ${c.last_weaned}두`}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {c.reasons.map((r) => (
                      <span
                        key={r}
                        className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-red-50 text-danger border border-red-200"
                      >
                        {CULL_REASON_LABELS[r] ?? r}
                      </span>
                    ))}
                  </div>
                </div>
                <Link
                  href={`/sows/${c.sow_id}`}
                  className="inline-flex items-center gap-1 text-text3 text-xs font-semibold hover:text-text shrink-0"
                >
                  상세
                  <ArrowRight className="w-3 h-3" />
                </Link>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
