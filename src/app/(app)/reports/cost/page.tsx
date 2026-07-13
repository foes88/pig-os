"use client";

import { useState } from "react";
import { useLocale } from "next-intl";
import { useQuery } from "@tanstack/react-query";
import { Wallet, TrendingUp, TrendingDown, PiggyBank } from "lucide-react";
import { localToday } from "@/lib/date";
import { downloadCsv } from "@/lib/utils/csv";
import { ReportsTabs } from "@/components/ReportsTabs";
import { ReportExportBar } from "@/components/ReportExportBar";
import { reportsApi } from "@/lib/api/endpoints/reports";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";
import type { CostSummary } from "@/types/api.types";

// 자족적 다국어(신규 페이지 — messages 부분갱신 대신 인라인 7개어, data-monitor와 동일 패턴).
const T: Record<string, {
  title: string; sub: string; feedCost: string; revenue: string; net: string; coverage: string;
  period: string; currency: string; feedQty: string; saleHead: string; noData: string;
  selectFarm: string; coverageNote: string; p6m: string; p1y: string; p2y: string;
}> = {
  en: { title: "Cost / Revenue", sub: "Feed cost (entered) vs. sales revenue, by currency.", feedCost: "Feed cost", revenue: "Sales revenue", net: "Net", coverage: "Cost coverage", period: "Period", currency: "Currency", feedQty: "Feed (kg)", saleHead: "Sold (head)", noData: "No feed or sales data in this period.", selectFarm: "Select a farm.", coverageNote: "Only feed records with a unit cost are counted toward cost. Net excludes feed without entered cost.", p6m: "6 mo", p1y: "1 yr", p2y: "2 yr" },
  ko: { title: "원가 · 수익", sub: "입력된 사료비 대비 판매수익 — 통화별.", feedCost: "사료비", revenue: "판매수익", net: "순이익", coverage: "원가 입력률", period: "기간", currency: "통화", feedQty: "사료(kg)", saleHead: "판매(두)", noData: "이 기간에 사료·판매 데이터가 없습니다.", selectFarm: "농장을 선택하세요.", coverageNote: "단가가 입력된 사료 기록만 원가에 반영됩니다. 순이익은 단가 미입력 사료를 제외합니다.", p6m: "6개월", p1y: "1년", p2y: "2년" },
  zh: { title: "成本 · 收益", sub: "已录入的饲料成本与销售收入对比（按货币）。", feedCost: "饲料成本", revenue: "销售收入", net: "净利", coverage: "成本录入率", period: "期间", currency: "货币", feedQty: "饲料(kg)", saleHead: "售出(头)", noData: "本期无饲料或销售数据。", selectFarm: "请选择农场。", coverageNote: "仅计入已录入单价的饲料记录。净利不含未录入单价的饲料。", p6m: "6个月", p1y: "1年", p2y: "2年" },
  es: { title: "Costo · Ingreso", sub: "Costo de alimento (registrado) vs. ingreso por ventas, por moneda.", feedCost: "Costo alimento", revenue: "Ingreso ventas", net: "Neto", coverage: "Cobertura de costo", period: "Periodo", currency: "Moneda", feedQty: "Alimento (kg)", saleHead: "Vendidos", noData: "Sin datos de alimento o ventas en este periodo.", selectFarm: "Seleccione una granja.", coverageNote: "Solo los registros de alimento con costo unitario cuentan como costo. El neto excluye el alimento sin costo registrado.", p6m: "6 m", p1y: "1 a", p2y: "2 a" },
  vi: { title: "Chi phí · Doanh thu", sub: "Chi phí thức ăn (đã nhập) so với doanh thu bán, theo tiền tệ.", feedCost: "Chi phí TĂ", revenue: "Doanh thu", net: "Lãi ròng", coverage: "Tỷ lệ nhập chi phí", period: "Kỳ", currency: "Tiền tệ", feedQty: "TĂ (kg)", saleHead: "Đã bán", noData: "Không có dữ liệu thức ăn hoặc bán trong kỳ này.", selectFarm: "Chọn một trang trại.", coverageNote: "Chỉ bản ghi thức ăn có đơn giá mới tính vào chi phí. Lãi ròng loại trừ thức ăn chưa nhập giá.", p6m: "6 th", p1y: "1 năm", p2y: "2 năm" },
  th: { title: "ต้นทุน · รายได้", sub: "ต้นทุนอาหาร (ที่บันทึก) เทียบกับรายได้จากการขาย แยกตามสกุลเงิน", feedCost: "ต้นทุนอาหาร", revenue: "รายได้ขาย", net: "สุทธิ", coverage: "ความครบของต้นทุน", period: "ช่วง", currency: "สกุลเงิน", feedQty: "อาหาร (kg)", saleHead: "ขาย (ตัว)", noData: "ไม่มีข้อมูลอาหารหรือการขายในช่วงนี้", selectFarm: "เลือกฟาร์ม", coverageNote: "นับเฉพาะบันทึกอาหารที่มีต้นทุนต่อหน่วย รายได้สุทธิไม่รวมอาหารที่ยังไม่ได้ใส่ต้นทุน", p6m: "6 ด.", p1y: "1 ปี", p2y: "2 ปี" },
  pt: { title: "Custo · Receita", sub: "Custo de ração (registrado) vs. receita de vendas, por moeda.", feedCost: "Custo ração", revenue: "Receita vendas", net: "Líquido", coverage: "Cobertura de custo", period: "Período", currency: "Moeda", feedQty: "Ração (kg)", saleHead: "Vendidos", noData: "Sem dados de ração ou vendas neste período.", selectFarm: "Selecione uma granja.", coverageNote: "Apenas registros de ração com custo unitário contam como custo. O líquido exclui ração sem custo registrado.", p6m: "6 m", p1y: "1 a", p2y: "2 a" },
};

function monthsAgoISO(n: number): string {
  const d = new Date();
  d.setMonth(d.getMonth() - n);
  return d.toISOString().slice(0, 10);
}
const TODAY = localToday();

const PRESETS = [
  { key: "p6m" as const, months: 6 },
  { key: "p1y" as const, months: 12 },
  { key: "p2y" as const, months: 24 },
];

function money(v: number | null, ccy: string): string {
  if (v == null) return "-";
  return `${ccy} ${v.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

export default function CostReportPage() {
  const locale = useLocale();
  const c = T[locale] ?? T.en;
  const farmId = useAuthStore((s) => s.activeFarmId);
  const [months, setMonths] = useState(12);
  const start = monthsAgoISO(months);

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.reports.costSummary(farmId ?? "", start, TODAY, "monthly"),
    queryFn: () => reportsApi.costSummary(farmId!, start, TODAY, "monthly"),
    enabled: !!farmId,
  });

  if (!farmId) return <div className="p-7 text-text3">{c.selectFarm}</div>;

  const summary: CostSummary | undefined = data;
  const byCcy = summary?.by_currency ?? [];
  const rows = summary?.rows ?? [];
  const hasData = rows.length > 0;

  const exportCsv = () => {
    downloadCsv(
      `pigos_cost_${start}_${TODAY}.csv`,
      [c.period, c.currency, c.feedCost, c.feedQty, c.saleHead, c.revenue, c.net],
      rows.map((r) => [
        r.period, r.currency, r.feed_cost, r.feed_qty_kg, r.sale_head, r.sale_revenue, r.net,
      ]),
    );
  };

  return (
    <div className="p-7 max-w-5xl print-area">
      <div className="no-print"><ReportsTabs /></div>
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-[22px] font-extrabold tracking-tight">{c.title}</h1>
          <p className="text-xs text-text3 mt-0.5">{c.sub}</p>
        </div>
        <ReportExportBar onCsv={exportCsv} csvDisabled={!hasData} />
      </div>

      <div className="flex gap-2 mb-5">
        {PRESETS.map((p) => (
          <button
            key={p.months}
            onClick={() => setMonths(p.months)}
            className={`text-xs font-semibold rounded-full px-3.5 py-1.5 border transition ${
              months === p.months
                ? "bg-primary text-white border-primary"
                : "border-border text-text3 hover:border-primary"
            }`}
          >
            {c[p.key]}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="h-40 bg-border rounded-2xl animate-pulse" />
      ) : !hasData ? (
        <div className="border border-border rounded-2xl py-16 text-center text-text3">{c.noData}</div>
      ) : (
        <>
          {/* 통화별 요약 카드 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5 mb-6">
            {byCcy.map((cy) => {
              const netPos = cy.net != null && cy.net >= 0;
              return (
                <div key={cy.currency} className="bg-surface border border-border rounded-2xl p-5" style={{ boxShadow: "var(--shadow-card)" }}>
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-mono text-sm font-bold text-text3">{cy.currency}</span>
                    <PiggyBank size={18} className="text-primary" />
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <div className="flex items-center gap-1 text-[11px] text-text3 mb-0.5"><Wallet size={11} />{c.feedCost}</div>
                      <div className="font-mono text-lg font-extrabold text-danger">{money(cy.feed_cost, cy.currency)}</div>
                    </div>
                    <div>
                      <div className="flex items-center gap-1 text-[11px] text-text3 mb-0.5"><TrendingUp size={11} />{c.revenue}</div>
                      <div className="font-mono text-lg font-extrabold text-success">{money(cy.sale_revenue, cy.currency)}</div>
                    </div>
                    <div>
                      <div className="flex items-center gap-1 text-[11px] text-text3 mb-0.5">
                        {netPos ? <TrendingUp size={11} /> : <TrendingDown size={11} />}{c.net}
                      </div>
                      <div className={`font-mono text-lg font-extrabold ${netPos ? "text-success" : "text-danger"}`}>
                        {money(cy.net, cy.currency)}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* 원가 입력률 안내 */}
          {summary?.feed_cost_coverage != null && summary.feed_cost_coverage < 100 && (
            <div className="bg-amber-soft border border-warning/40 rounded-xl p-3.5 mb-6 text-xs text-warning">
              <span className="font-bold">{c.coverage}: {summary.feed_cost_coverage}%</span>
              <span className="ml-1">({summary.feed_records_with_cost}/{summary.feed_records_total}) — {c.coverageNote}</span>
            </div>
          )}

          {/* 기간×통화 상세 테이블 */}
          <div className="border border-border rounded-2xl overflow-x-auto">
            <table className="w-full text-sm min-w-[640px]">
              <thead>
                <tr className="bg-bg2 text-text3 text-[11px] uppercase tracking-wide">
                  <th className="text-left font-semibold px-3 py-2.5">{c.period}</th>
                  <th className="text-left font-semibold px-3 py-2.5">{c.currency}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{c.feedQty}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{c.feedCost}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{c.saleHead}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{c.revenue}</th>
                  <th className="text-right font-semibold px-3 py-2.5">{c.net}</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => {
                  const netPos = r.net != null && r.net >= 0;
                  return (
                    <tr key={`${r.period}-${r.currency}`} className="border-t border-border">
                      <td className="px-3 py-2.5 font-mono text-xs text-text2">{r.period}</td>
                      <td className="px-3 py-2.5 font-mono text-xs">{r.currency}</td>
                      <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.feed_qty_kg.toLocaleString()}</td>
                      <td className="px-3 py-2.5 text-right font-mono tabular-nums text-danger">{r.feed_cost != null ? r.feed_cost.toLocaleString() : "-"}</td>
                      <td className="px-3 py-2.5 text-right font-mono tabular-nums">{r.sale_head}</td>
                      <td className="px-3 py-2.5 text-right font-mono tabular-nums text-success">{r.sale_revenue != null ? r.sale_revenue.toLocaleString() : "-"}</td>
                      <td className={`px-3 py-2.5 text-right font-mono tabular-nums font-semibold ${netPos ? "text-success" : "text-danger"}`}>
                        {r.net != null ? r.net.toLocaleString() : "-"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
