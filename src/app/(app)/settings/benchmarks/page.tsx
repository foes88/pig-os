"use client";

import { useQuery } from "@tanstack/react-query";
import { farmsApi } from "@/lib/api/endpoints/farms";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";

// Reference benchmark targets per market (read-only; from SCREEN_MENU_SPEC / regional refs).
const BENCHMARKS: { kpi: string; unit: string; kr: string; us: string; br: string; cn: string }[] = [
  { kpi: "PSY",            unit: "두/년", kr: "24.0", us: "26.0", br: "27.0", cn: "22.0" },
  { kpi: "NPD",            unit: "일",   kr: "35",   us: "32",   br: "30",   cn: "45" },
  { kpi: "분만율 (FR)",     unit: "%",    kr: "85",   us: "88",   br: "87",   cn: "82" },
  { kpi: "이유두수 (WPL)",  unit: "두",   kr: "11.5", us: "11.0", br: "11.8", cn: "10.5" },
];

export default function BenchmarksPage() {
  const farmId = useAuthStore((s) => s.activeFarmId);

  const { data: repro } = useQuery({
    queryKey: queryKeys.farms.reproConfig(farmId ?? ""),
    queryFn: () => farmsApi.getReproConfig(farmId!),
    enabled: !!farmId,
  });

  return (
    <div className="max-w-2xl mx-auto px-7 py-6">
      <h1 className="text-xl font-extrabold tracking-tight text-text mb-1">벤치마크</h1>
      <p className="text-[13px] text-text3 mb-6">국가별 KPI 목표값 (참고용, 읽기 전용)</p>

      <div className="border border-border rounded-2xl overflow-hidden mb-6">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-bg2 text-text3 text-[11px] uppercase tracking-wide">
              <th className="text-left font-semibold px-4 py-2.5">KPI</th>
              <th className="text-right font-semibold px-4 py-2.5">KR</th>
              <th className="text-right font-semibold px-4 py-2.5">US</th>
              <th className="text-right font-semibold px-4 py-2.5">BR</th>
              <th className="text-right font-semibold px-4 py-2.5">CN</th>
            </tr>
          </thead>
          <tbody>
            {BENCHMARKS.map((b) => (
              <tr key={b.kpi} className="border-t border-border">
                <td className="px-4 py-2.5 font-semibold text-text">
                  {b.kpi} <span className="text-text3 font-normal text-xs">({b.unit})</span>
                </td>
                <td className="px-4 py-2.5 text-right font-mono">{b.kr}</td>
                <td className="px-4 py-2.5 text-right font-mono">{b.us}</td>
                <td className="px-4 py-2.5 text-right font-mono">{b.br}</td>
                <td className="px-4 py-2.5 text-right font-mono">{b.cn}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {repro && (
        <div>
          <div className="px-1 pb-2 text-[11px] font-bold text-text3 uppercase tracking-widest">
            현재 농장 설정값
          </div>
          <div className="bg-surface border border-border rounded-2xl px-5 py-4 text-sm text-text2 space-y-1 font-mono">
            <div>임신 {repro.gestation_days}일 · 포유 {repro.lactation_days}일 · WSI {repro.wei_target_days}일</div>
            <div>후보돈 초교배 {repro.gilt_first_mating_age}일 · 출하 {repro.slaughter_age}일</div>
          </div>
        </div>
      )}
    </div>
  );
}
