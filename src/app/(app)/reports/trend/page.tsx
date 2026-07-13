"use client";

import { useState } from "react";
import { useLocale } from "next-intl";
import { useQuery } from "@tanstack/react-query";
import { TrendingUp } from "lucide-react";
import { ReportsTabs } from "@/components/ReportsTabs";
import { ReportExportBar } from "@/components/ReportExportBar";
import { downloadCsv } from "@/lib/utils/csv";
import { reportsApi } from "@/lib/api/endpoints/reports";
import { useAuthStore } from "@/store/auth.store";
import type { AnnualKpiRow } from "@/types/api.types";

// 자족적 다국어(신규 리포트 — messages 부분갱신 대신 인라인, cost/data-monitor와 동일 패턴).
const T: Record<string, Record<string, string>> = {
  en: { title: "PSY / NPD Trend", sub: "Year-over-year sow productivity vs. country targets.", psy: "PSY", npd: "NPD", fr: "Farrowing rate", year: "Year", avgSows: "Avg sows", weaned: "Weaned", farrowings: "Farrowings", matings: "Matings", target: "Target", bench: "Country benchmarks (target)", noData: "No yearly data yet.", selectFarm: "Select a farm.", y3: "3 yr", y5: "5 yr", y10: "10 yr", higher: "higher is better", lower: "lower is better" },
  ko: { title: "PSY / NPD 추세", sub: "연도별 모돈 생산성 — 국가 목표 대비.", psy: "PSY", npd: "NPD", fr: "분만율", year: "연도", avgSows: "평균모돈", weaned: "이유두수", farrowings: "분만복수", matings: "교배복수", target: "목표", bench: "국가 벤치마크(목표)", noData: "연도별 데이터가 아직 없습니다.", selectFarm: "농장을 선택하세요.", y3: "3년", y5: "5년", y10: "10년", higher: "높을수록 좋음", lower: "낮을수록 좋음" },
  zh: { title: "PSY / NPD 趋势", sub: "母猪年度生产力与国家目标对比。", psy: "PSY", npd: "NPD", fr: "分娩率", year: "年度", avgSows: "平均母猪", weaned: "断奶", farrowings: "分娩", matings: "配种", target: "目标", bench: "国家基准(目标)", noData: "暂无年度数据。", selectFarm: "请选择农场。", y3: "3年", y5: "5年", y10: "10年", higher: "越高越好", lower: "越低越好" },
  es: { title: "Tendencia PSY / NPD", sub: "Productividad anual de cerdas vs. objetivos por país.", psy: "PSY", npd: "NPD", fr: "Tasa de partos", year: "Año", avgSows: "Prom. cerdas", weaned: "Destetados", farrowings: "Partos", matings: "Montas", target: "Objetivo", bench: "Referencias por país (objetivo)", noData: "Aún no hay datos anuales.", selectFarm: "Seleccione una granja.", y3: "3 años", y5: "5 años", y10: "10 años", higher: "más alto es mejor", lower: "más bajo es mejor" },
  vi: { title: "Xu hướng PSY / NPD", sub: "Năng suất nái theo năm so với mục tiêu quốc gia.", psy: "PSY", npd: "NPD", fr: "Tỷ lệ đẻ", year: "Năm", avgSows: "TB nái", weaned: "Cai sữa", farrowings: "Số lứa đẻ", matings: "Phối", target: "Mục tiêu", bench: "Chuẩn quốc gia (mục tiêu)", noData: "Chưa có dữ liệu theo năm.", selectFarm: "Chọn một trang trại.", y3: "3 năm", y5: "5 năm", y10: "10 năm", higher: "cao hơn tốt hơn", lower: "thấp hơn tốt hơn" },
  th: { title: "แนวโน้ม PSY / NPD", sub: "ผลผลิตแม่สุกรรายปีเทียบเป้าหมายประเทศ", psy: "PSY", npd: "NPD", fr: "อัตราการคลอด", year: "ปี", avgSows: "เฉลี่ยแม่", weaned: "หย่านม", farrowings: "คลอด", matings: "ผสม", target: "เป้า", bench: "เกณฑ์ประเทศ (เป้า)", noData: "ยังไม่มีข้อมูลรายปี", selectFarm: "เลือกฟาร์ม", y3: "3 ปี", y5: "5 ปี", y10: "10 ปี", higher: "ยิ่งสูงยิ่งดี", lower: "ยิ่งต่ำยิ่งดี" },
  pt: { title: "Tendência PSY / NPD", sub: "Produtividade anual das matrizes vs. metas por país.", psy: "PSY", npd: "NPD", fr: "Taxa de parto", year: "Ano", avgSows: "Média matrizes", weaned: "Desmamados", farrowings: "Partos", matings: "Cobrições", target: "Meta", bench: "Referências por país (meta)", noData: "Ainda não há dados anuais.", selectFarm: "Selecione uma granja.", y3: "3 anos", y5: "5 anos", y10: "10 anos", higher: "maior é melhor", lower: "menor é melhor" },
  ru: { title: "Динамика PSY / NPD", sub: "Годовая продуктивность свиноматок и целевые показатели страны.", psy: "PSY", npd: "NPD", fr: "Опорос %", year: "Год", avgSows: "Ср. маток", weaned: "Отъём", farrowings: "Опоросы", matings: "Осеменения", target: "Цель", bench: "Ориентиры по странам (цель)", noData: "Пока нет годовых данных.", selectFarm: "Выберите ферму.", y3: "3 г", y5: "5 л", y10: "10 л", higher: "больше — лучше", lower: "меньше — лучше" },
};

const PRESETS = [
  { key: "y3", years: 3 },
  { key: "y5", years: 5 },
  { key: "y10", years: 10 },
];

// ── 인라인 SVG 라인차트 (외부 차트 라이브러리 없음) ──
function LineChart({
  points,
  benchmark,
  color,
  label,
}: {
  points: { x: string; y: number | null }[];
  benchmark?: number | null;
  color: string;
  label: string;
}) {
  const W = 320, H = 120, padX = 8, padTop = 12, padBottom = 20;
  const vals = points.map((p) => p.y).filter((v): v is number => v != null);
  const withBench = benchmark != null ? [...vals, benchmark] : vals;
  if (vals.length === 0) {
    return <div className="h-[120px] flex items-center justify-center text-xs text-text3">—</div>;
  }
  const lo = Math.min(...withBench), hi = Math.max(...withBench);
  const span = hi - lo || 1;
  const plotH = H - padTop - padBottom;
  const stepX = points.length > 1 ? (W - padX * 2) / (points.length - 1) : 0;
  const xAt = (i: number) => padX + stepX * i;
  const yAt = (v: number) => padTop + plotH * (1 - (v - lo) / span);

  // null 은 선을 끊는다(연속 구간만 polyline)
  const segments: string[] = [];
  let cur: string[] = [];
  points.forEach((p, i) => {
    if (p.y == null) { if (cur.length) { segments.push(cur.join(" ")); cur = []; } return; }
    cur.push(`${xAt(i).toFixed(1)},${yAt(p.y).toFixed(1)}`);
  });
  if (cur.length) segments.push(cur.join(" "));

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-[120px]" role="img" aria-label={label}>
      {benchmark != null && (
        <>
          <line x1={padX} x2={W - padX} y1={yAt(benchmark)} y2={yAt(benchmark)}
            stroke="var(--color-warning, #d97706)" strokeWidth="1" strokeDasharray="4 3" opacity="0.7" />
          <text x={W - padX} y={yAt(benchmark) - 3} textAnchor="end"
            className="fill-warning" fontSize="9">{benchmark}</text>
        </>
      )}
      {segments.map((pts, i) => (
        <polyline key={i} points={pts} fill="none" stroke={color} strokeWidth="2"
          strokeLinejoin="round" strokeLinecap="round" />
      ))}
      {points.map((p, i) => p.y != null && (
        <g key={i}>
          <circle cx={xAt(i)} cy={yAt(p.y)} r="3" fill={color} />
          <text x={xAt(i)} y={yAt(p.y) - 6} textAnchor="middle" fontSize="9" className="fill-text2 font-mono">{p.y}</text>
        </g>
      ))}
      {points.map((p, i) => (
        <text key={`x${i}`} x={xAt(i)} y={H - 6} textAnchor="middle" fontSize="9" className="fill-text3 font-mono">
          {p.x}
        </text>
      ))}
    </svg>
  );
}

export default function KpiTrendPage() {
  const locale = useLocale();
  const c = T[locale] ?? T.en;
  const farmId = useAuthStore((s) => s.activeFarmId);
  const [years, setYears] = useState(5);

  const { data, isLoading } = useQuery({
    queryKey: ["reports", "annual-kpi", farmId, years],
    queryFn: () => reportsApi.annualKpi(farmId!, years),
    enabled: !!farmId,
  });

  if (!farmId) return <div className="p-7 text-text3">{c.selectFarm}</div>;

  const rows: AnnualKpiRow[] = data?.rows ?? [];
  const hasData = rows.some((r) => r.psy != null || r.npd != null);
  // 농장 국가 목표(추세 차트 기준선)
  const ownBench = data?.country_benchmarks?.find((b) => b.country === data?.country_scope)
    ?? data?.country_benchmarks?.[0];

  const exportCsv = () => {
    downloadCsv(
      `pigos_kpi_trend_${farmId}_${years}y.csv`,
      [c.year, c.psy, c.npd, `${c.fr}(%)`, c.farrowings, c.matings, c.avgSows, c.weaned],
      rows.map((r) => [r.year, r.psy, r.npd, r.farrowing_rate, r.total_farrowings, r.total_matings, r.avg_sows, r.total_weaned]),
    );
  };

  const psyPts = rows.map((r) => ({ x: String(r.year), y: r.psy }));
  const npdPts = rows.map((r) => ({ x: String(r.year), y: r.npd }));

  return (
    <div className="p-7 max-w-5xl print-area">
      <div className="no-print"><ReportsTabs /></div>
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-[22px] font-extrabold tracking-tight flex items-center gap-2">
            <TrendingUp size={20} className="text-primary" />{c.title}
          </h1>
          <p className="text-xs text-text3 mt-0.5">{c.sub}</p>
        </div>
        <ReportExportBar onCsv={exportCsv} csvDisabled={!hasData} />
      </div>

      <div className="no-print flex gap-2 mb-5">
        {PRESETS.map((p) => (
          <button
            key={p.years}
            onClick={() => setYears(p.years)}
            className={`text-xs font-semibold rounded-full px-3.5 py-1.5 border transition ${
              years === p.years ? "bg-primary text-white border-primary" : "border-border text-text3 hover:border-primary"
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
          {/* 추세 차트 2종 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div className="bg-surface border border-border rounded-2xl p-4">
              <div className="flex items-baseline justify-between mb-1">
                <h2 className="text-sm font-bold">{c.psy}</h2>
                <span className="text-[10px] text-success">{c.higher}</span>
              </div>
              <LineChart points={psyPts} benchmark={ownBench?.psy} color="var(--color-primary, #2563eb)" label={c.psy} />
            </div>
            <div className="bg-surface border border-border rounded-2xl p-4">
              <div className="flex items-baseline justify-between mb-1">
                <h2 className="text-sm font-bold">{c.npd}</h2>
                <span className="text-[10px] text-text3">{c.lower}</span>
              </div>
              <LineChart points={npdPts} benchmark={ownBench?.npd} color="var(--color-purple, #7c3aed)" label={c.npd} />
            </div>
          </div>

          {/* 국가 벤치마크 병기 */}
          {(data?.country_benchmarks?.length ?? 0) > 0 && (
            <div className="bg-surface border border-border rounded-2xl overflow-x-auto mb-6">
              <div className="px-4 pt-3 pb-1 text-xs font-bold text-text3">{c.bench}</div>
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-bg2 text-text3 text-[11px] uppercase tracking-wide">
                    <th className="text-left font-semibold px-4 py-2">{c.year}</th>
                    {data!.country_benchmarks.map((b) => (
                      <th key={b.country} className="text-right font-semibold px-4 py-2 font-mono">{b.country}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {([["psy", c.psy], ["npd", c.npd], ["farrowing_rate", c.fr]] as const).map(([k, lbl]) => (
                    <tr key={k} className="border-t border-border">
                      <td className="px-4 py-2 font-semibold">{lbl} {c.target}</td>
                      {data!.country_benchmarks.map((b) => (
                        <td key={b.country} className="px-4 py-2 text-right font-mono tabular-nums text-text2">
                          {b[k] != null ? (k === "farrowing_rate" ? `${b[k]}%` : b[k]) : "-"}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* 연도별 데이터 표 */}
          <div className="border border-border rounded-2xl overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-bg2 text-text3 text-[11px] uppercase tracking-wide">
                  <th className="text-left font-semibold px-3 py-2.5">{c.year}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{c.psy}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{c.npd}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{c.fr}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{c.farrowings}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{c.matings}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{c.avgSows}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{c.weaned}</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.year} className="border-t border-border">
                    <td className="px-3 py-2.5 font-mono font-semibold">{r.year}</td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.psy ?? "-"}</td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.npd ?? "-"}</td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.farrowing_rate != null ? `${r.farrowing_rate}%` : "-"}</td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.total_farrowings}</td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.total_matings}</td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.avg_sows ?? "-"}</td>
                    <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.total_weaned}</td>
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
