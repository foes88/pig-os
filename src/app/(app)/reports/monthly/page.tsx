"use client";

import { useState } from "react";
import { useLocale } from "next-intl";
import { useQuery } from "@tanstack/react-query";
import { CalendarRange, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { ReportsTabs } from "@/components/ReportsTabs";
import { ReportExportBar } from "@/components/ReportExportBar";
import { MiniLineChart } from "@/components/MiniLineChart";
import { downloadCsv } from "@/lib/utils/csv";
import { localToday } from "@/lib/date";
import { reportsApi } from "@/lib/api/endpoints/reports";
import { kpiApi } from "@/lib/api/endpoints/kpi";
import { useAuthStore } from "@/store/auth.store";
import type { KpiTrend, ReproductionRow } from "@/types/api.types";

// 자족적 다국어(신규 리포트 — 인라인, cost/trend와 동일 패턴).
const T: Record<string, Record<string, string>> = {
  en: { title: "Monthly Dashboard", sub: "Headline KPIs and volumes, month by month.", psy: "PSY", npd: "NPD", fr: "Farrowing rate", month: "Month", matings: "Matings", farrowings: "Farrowings", weanings: "Weanings", tb: "Avg TB", ba: "Avg BA", weaned: "Avg weaned", latest: "Latest month", noData: "No monthly data yet.", selectFarm: "Select a farm.", m6: "6 mo", m12: "12 mo", m24: "24 mo", volumes: "Monthly volumes" },
  ko: { title: "월별 종합 대시보드", sub: "핵심 KPI와 물량을 월별로 한눈에.", psy: "PSY", npd: "NPD", fr: "분만율", month: "월", matings: "교배", farrowings: "분만", weanings: "이유", tb: "평균총산", ba: "평균실산", weaned: "평균이유", latest: "최근 월", noData: "월별 데이터가 아직 없습니다.", selectFarm: "농장을 선택하세요.", m6: "6개월", m12: "12개월", m24: "24개월", volumes: "월별 물량" },
  zh: { title: "月度综合看板", sub: "核心KPI与产量，逐月一览。", psy: "PSY", npd: "NPD", fr: "分娩率", month: "月", matings: "配种", farrowings: "分娩", weanings: "断奶", tb: "平均总产", ba: "平均活产", weaned: "平均断奶", latest: "最近月", noData: "暂无月度数据。", selectFarm: "请选择农场。", m6: "6个月", m12: "12个月", m24: "24个月", volumes: "月度产量" },
  es: { title: "Panel mensual", sub: "KPIs y volúmenes clave, mes a mes.", psy: "PSY", npd: "NPD", fr: "Tasa de partos", month: "Mes", matings: "Montas", farrowings: "Partos", weanings: "Destetes", tb: "TN prom.", ba: "NV prom.", weaned: "Destetados prom.", latest: "Último mes", noData: "Aún no hay datos mensuales.", selectFarm: "Seleccione una granja.", m6: "6 m", m12: "12 m", m24: "24 m", volumes: "Volúmenes mensuales" },
  vi: { title: "Bảng điều khiển tháng", sub: "KPI và sản lượng chính, theo từng tháng.", psy: "PSY", npd: "NPD", fr: "Tỷ lệ đẻ", month: "Tháng", matings: "Phối", farrowings: "Đẻ", weanings: "Cai sữa", tb: "TB tổng đẻ", ba: "TB đẻ sống", weaned: "TB cai sữa", latest: "Tháng gần nhất", noData: "Chưa có dữ liệu tháng.", selectFarm: "Chọn một trang trại.", m6: "6 th", m12: "12 th", m24: "24 th", volumes: "Sản lượng tháng" },
  th: { title: "แดชบอร์ดรายเดือน", sub: "KPI หลักและปริมาณ รายเดือน", psy: "PSY", npd: "NPD", fr: "อัตราการคลอด", month: "เดือน", matings: "ผสม", farrowings: "คลอด", weanings: "หย่านม", tb: "เกิดรวมเฉลี่ย", ba: "เกิดมีชีวิตเฉลี่ย", weaned: "หย่านมเฉลี่ย", latest: "เดือนล่าสุด", noData: "ยังไม่มีข้อมูลรายเดือน", selectFarm: "เลือกฟาร์ม", m6: "6 ด.", m12: "12 ด.", m24: "24 ด.", volumes: "ปริมาณรายเดือน" },
  pt: { title: "Painel mensal", sub: "KPIs e volumes principais, mês a mês.", psy: "PSY", npd: "NPD", fr: "Taxa de parto", month: "Mês", matings: "Cobrições", farrowings: "Partos", weanings: "Desmames", tb: "NT méd.", ba: "NV méd.", weaned: "Desmam. méd.", latest: "Último mês", noData: "Ainda não há dados mensais.", selectFarm: "Selecione uma granja.", m6: "6 m", m12: "12 m", m24: "24 m", volumes: "Volumes mensais" },
  ru: { title: "Месячная панель", sub: "Ключевые KPI и объёмы по месяцам.", psy: "PSY", npd: "NPD", fr: "Опорос %", month: "Месяц", matings: "Осеменения", farrowings: "Опоросы", weanings: "Отъёмы", tb: "Ср. всего", ba: "Ср. живых", weaned: "Ср. отъём", latest: "Последний месяц", noData: "Пока нет месячных данных.", selectFarm: "Выберите ферму.", m6: "6 мес", m12: "12 мес", m24: "24 мес", volumes: "Месячные объёмы" },
};

const PRESETS = [
  { key: "m6", months: 6 },
  { key: "m12", months: 12 },
  { key: "m24", months: 24 },
];

function monthsAgoISO(n: number): string {
  const d = new Date();
  d.setMonth(d.getMonth() - n);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-01`;
}

// 최근 월 vs 직전 월 방향 표시 (higherBetter=true → 상승이 좋음)
function Delta({ cur, prev, higherBetter }: { cur: number | null; prev: number | null; higherBetter: boolean }) {
  if (cur == null || prev == null || cur === prev) return <Minus size={14} className="text-text3" />;
  const up = cur > prev;
  const good = up === higherBetter;
  const Icon = up ? TrendingUp : TrendingDown;
  return <Icon size={14} className={good ? "text-success" : "text-danger"} />;
}

export default function MonthlyDashboardPage() {
  const locale = useLocale();
  const c = T[locale] ?? T.en;
  const farmId = useAuthStore((s) => s.activeFarmId);
  const [months, setMonths] = useState(12);

  const trendQ = useQuery({
    queryKey: ["reports", "monthly-trend", farmId, months],
    queryFn: () => kpiApi.trend(farmId!, "psy", months),
    enabled: !!farmId,
  });
  const prodQ = useQuery({
    queryKey: ["reports", "monthly-prod", farmId, months],
    queryFn: () => reportsApi.productionSummary(farmId!, monthsAgoISO(months - 1), localToday(), "monthly", "period"),
    enabled: !!farmId,
  });

  if (!farmId) return <div className="p-7 text-text3">{c.selectFarm}</div>;

  const trend: KpiTrend[] = trendQ.data ?? [];
  const prod: ReproductionRow[] = prodQ.data?.rows ?? [];
  const isLoading = trendQ.isLoading || prodQ.isLoading;
  const hasData = trend.some((t) => t.psy != null || t.npd != null) || prod.length > 0;

  const last = trend[trend.length - 1];
  const prev = trend[trend.length - 2];

  const exportCsv = () => {
    // 추세(KPI) + 물량을 월 키로 병합
    const prodByMonth = new Map(prod.map((r) => [r.period, r]));
    const allMonths = Array.from(new Set([...trend.map((t) => t.period), ...prod.map((r) => r.period)])).sort();
    downloadCsv(
      `pigos_monthly_${farmId}_${allMonths.length}mo.csv`,
      [c.month, c.psy, c.npd, `${c.fr}(%)`, c.matings, c.farrowings, c.weanings, c.tb, c.ba, c.weaned],
      allMonths.map((m) => {
        const t = trend.find((x) => x.period === m);
        const p = prodByMonth.get(m);
        return [m, t?.psy ?? null, t?.npd ?? null, t?.farrowing_rate ?? null,
          p?.total_matings ?? null, p?.total_farrowings ?? null, p?.total_weanings ?? null,
          p?.avg_tb ?? null, p?.avg_ba ?? null, p?.avg_weaned ?? null];
      }),
    );
  };

  const psyPts = trend.map((t) => ({ x: t.period.slice(2), y: t.psy }));
  const npdPts = trend.map((t) => ({ x: t.period.slice(2), y: t.npd }));
  const frPts = trend.map((t) => ({ x: t.period.slice(2), y: t.farrowing_rate }));

  return (
    <div className="p-7 max-w-5xl print-area">
      <div className="no-print"><ReportsTabs /></div>
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-[22px] font-extrabold tracking-tight flex items-center gap-2">
            <CalendarRange size={20} className="text-primary" />{c.title}
          </h1>
          <p className="text-xs text-text3 mt-0.5">{c.sub}</p>
        </div>
        <ReportExportBar onCsv={exportCsv} csvDisabled={!hasData} />
      </div>

      <div className="no-print flex gap-2 mb-5">
        {PRESETS.map((p) => (
          <button
            key={p.months}
            onClick={() => setMonths(p.months)}
            className={`text-xs font-semibold rounded-full px-3.5 py-1.5 border transition ${
              months === p.months ? "bg-primary text-white border-primary" : "border-border text-text3 hover:border-primary"
            }`}
          >
            {c[p.key]}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="h-64 bg-border rounded-2xl animate-pulse" />
      ) : !hasData ? (
        <div className="border border-border rounded-2xl py-16 text-center text-text3">{c.noData}</div>
      ) : (
        <>
          {/* 최근 월 헤드라인 카드 */}
          {last && (
            <div className="grid grid-cols-3 gap-3 mb-6">
              {([
                { label: c.psy, cur: last.psy, prev: prev?.psy ?? null, higher: true },
                { label: c.npd, cur: last.npd, prev: prev?.npd ?? null, higher: false },
                { label: c.fr, cur: last.farrowing_rate, prev: prev?.farrowing_rate ?? null, higher: true, pct: true },
              ] as const).map((k) => (
                <div key={k.label} className="bg-surface border border-border rounded-2xl p-4">
                  <div className="text-[11px] font-bold uppercase tracking-wide text-text3 mb-1">{k.label}</div>
                  <div className="flex items-baseline gap-1.5">
                    <span className="font-mono text-2xl font-extrabold">{k.cur != null ? k.cur : "—"}{"pct" in k && k.pct && k.cur != null ? "%" : ""}</span>
                    <Delta cur={k.cur} prev={k.prev} higherBetter={k.higher} />
                  </div>
                  <div className="text-[10px] text-text3 mt-0.5">{c.latest} · {last.period}</div>
                </div>
              ))}
            </div>
          )}

          {/* 월별 추세 3종 */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-surface border border-border rounded-2xl p-4">
              <h2 className="text-sm font-bold mb-1">{c.psy}</h2>
              <MiniLineChart points={psyPts} color="var(--color-primary, #2563eb)" label={c.psy} />
            </div>
            <div className="bg-surface border border-border rounded-2xl p-4">
              <h2 className="text-sm font-bold mb-1">{c.npd}</h2>
              <MiniLineChart points={npdPts} color="var(--color-purple, #7c3aed)" label={c.npd} />
            </div>
            <div className="bg-surface border border-border rounded-2xl p-4">
              <h2 className="text-sm font-bold mb-1">{c.fr}</h2>
              <MiniLineChart points={frPts} color="var(--color-success, #16a34a)" label={c.fr} />
            </div>
          </div>

          {/* 월별 물량 표 */}
          <div className="border border-border rounded-2xl overflow-x-auto">
            <div className="px-4 pt-3 pb-1 text-xs font-bold text-text3">{c.volumes}</div>
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-bg2 text-text3 text-[11px] uppercase tracking-wide">
                  <th className="text-left font-semibold px-3 py-2.5">{c.month}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{c.matings}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{c.farrowings}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{c.weanings}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{c.tb}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{c.ba}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{c.weaned}</th>
                </tr>
              </thead>
              <tbody>
                {prod.map((r) => (
                  <tr key={r.period} className="border-t border-border">
                    <td className="px-3 py-2.5 font-mono font-semibold">{r.period}</td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.total_matings}</td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.total_farrowings}</td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.total_weanings}</td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.avg_tb ?? "-"}</td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.avg_ba ?? "-"}</td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.avg_weaned ?? "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
