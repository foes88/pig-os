"use client";

import { useQuery } from "@tanstack/react-query";
import { useLocale } from "next-intl";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, PiggyBank, Activity, Calendar } from "lucide-react";
import { adminApi } from "@/lib/api/endpoints/admin";

// 자족적 다국어(admin 인라인 7개어, data-monitor 목록과 동일 패턴).
const T: Record<string, Record<string, string>> = {
  en: { back: "Back to monitor", sows: "Sows", psy: "PSY (YTD)", weaned: "Weaned YTD", avgSows: "Avg sows", status: "Sow status", events: "Event activity", type: "Type", total: "Total", d30: "30d", last: "Last", recent: "Recent activity", none: "No activity yet", loading: "Loading…", org: "Org", country: "Country" },
  ko: { back: "모니터로", sows: "모돈", psy: "PSY(당해)", weaned: "당해 이유", avgSows: "평균모돈", status: "모돈 상태", events: "이벤트 활동", type: "유형", total: "전체", d30: "30일", last: "마지막", recent: "최근 활동", none: "활동 없음", loading: "로딩…", org: "조직", country: "국가" },
  zh: { back: "返回监控", sows: "母猪", psy: "PSY(年内)", weaned: "年内断奶", avgSows: "平均母猪", status: "母猪状态", events: "事件活动", type: "类型", total: "总计", d30: "30天", last: "最后", recent: "最近活动", none: "暂无活动", loading: "加载中…", org: "机构", country: "国家" },
  es: { back: "Volver", sows: "Cerdas", psy: "PSY (año)", weaned: "Destetados año", avgSows: "Prom. cerdas", status: "Estado cerdas", events: "Actividad", type: "Tipo", total: "Total", d30: "30d", last: "Último", recent: "Actividad reciente", none: "Sin actividad", loading: "Cargando…", org: "Org", country: "País" },
  vi: { back: "Quay lại", sows: "Nái", psy: "PSY (năm)", weaned: "Cai sữa năm", avgSows: "TB nái", status: "Trạng thái nái", events: "Hoạt động", type: "Loại", total: "Tổng", d30: "30n", last: "Gần nhất", recent: "Hoạt động gần đây", none: "Chưa có", loading: "Đang tải…", org: "Tổ chức", country: "Quốc gia" },
  th: { back: "กลับ", sows: "แม่สุกร", psy: "PSY (ปีนี้)", weaned: "หย่านมปีนี้", avgSows: "เฉลี่ยแม่", status: "สถานะแม่สุกร", events: "กิจกรรม", type: "ประเภท", total: "รวม", d30: "30 วัน", last: "ล่าสุด", recent: "กิจกรรมล่าสุด", none: "ยังไม่มี", loading: "กำลังโหลด…", org: "องค์กร", country: "ประเทศ" },
  pt: { back: "Voltar", sows: "Matrizes", psy: "PSY (ano)", weaned: "Desmame ano", avgSows: "Média matrizes", status: "Status matrizes", events: "Atividade", type: "Tipo", total: "Total", d30: "30d", last: "Último", recent: "Atividade recente", none: "Sem atividade", loading: "Carregando…", org: "Org", country: "País" },
};

const EVENT_LABEL: Record<string, string> = {
  mating: "🐷 교배", farrowing: "👶 분만", weaning: "🍼 이유", health: "💉 건강",
  removal: "📤 도폐사", piglet: "🐖 자돈", feed: "🌾 사료",
};

export default function FarmDataDetailPage() {
  const locale = useLocale();
  const c = T[locale] ?? T.en;
  const router = useRouter();
  const { farmId } = useParams<{ farmId: string }>();

  const { data, isLoading } = useQuery({
    queryKey: ["admin", "data-monitor", farmId],
    queryFn: () => adminApi.dataMonitorDetail(farmId),
    enabled: !!farmId,
  });

  return (
    <div className="p-7 max-w-5xl">
      <button onClick={() => router.push("/admin/data-monitor")}
        className="inline-flex items-center gap-1.5 text-xs text-text3 hover:text-text mb-4">
        <ArrowLeft size={14} /> {c.back}
      </button>

      {isLoading || !data ? (
        <div className="text-text3 text-sm">{c.loading}</div>
      ) : (
        <>
          {/* 헤더 */}
          <header className="mb-6">
            <h1 className="text-[22px] font-extrabold tracking-tight">{data.farm_name}</h1>
            <p className="text-xs text-text3 mt-0.5">
              {c.country} {data.country} · {c.org} {data.org_name ?? "—"} · {data.timezone} · {data.currency}
            </p>
          </header>

          {/* KPI 카드 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            {[
              { label: c.sows, value: data.total_sows, icon: PiggyBank },
              { label: c.psy, value: data.psy != null ? data.psy.toFixed(1) : "—", icon: Activity },
              { label: c.weaned, value: data.total_weaned_ytd.toLocaleString(), icon: Activity },
              { label: c.avgSows, value: data.avg_sows_ytd != null ? data.avg_sows_ytd.toFixed(0) : "—", icon: PiggyBank },
            ].map((k) => (
              <div key={k.label} className="bg-surface border border-border rounded-2xl p-4">
                <div className="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wide text-text3 mb-1.5">
                  <k.icon size={13} className="text-primary" />{k.label}
                </div>
                <div className="font-mono text-2xl font-extrabold text-text">{k.value}</div>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            {/* 모돈 상태분포 */}
            <div className="bg-surface border border-border rounded-2xl p-5">
              <h2 className="text-sm font-bold mb-3">{c.status}</h2>
              {data.sows_by_status.length === 0 ? (
                <p className="text-xs text-text3">{c.none}</p>
              ) : data.sows_by_status.map((s) => (
                <div key={s.status} className="flex items-center justify-between py-1 text-sm">
                  <span className="text-text2 font-mono text-xs">{s.status}</span>
                  <span className="font-mono font-bold">{s.count}</span>
                </div>
              ))}
            </div>

            {/* 이벤트 유형별 분해 */}
            <div className="bg-surface border border-border rounded-2xl p-5 md:col-span-2">
              <h2 className="text-sm font-bold mb-3">{c.events}</h2>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-[11px] uppercase tracking-wide text-text3">
                    <th className="text-left font-bold py-1">{c.type}</th>
                    <th className="text-right font-bold py-1">{c.total}</th>
                    <th className="text-right font-bold py-1">{c.d30}</th>
                    <th className="text-right font-bold py-1">{c.last}</th>
                  </tr>
                </thead>
                <tbody>
                  {data.event_breakdown.length === 0 ? (
                    <tr><td colSpan={4} className="py-4 text-center text-text3 text-xs">{c.none}</td></tr>
                  ) : data.event_breakdown.map((e) => (
                    <tr key={e.type} className="border-t border-border">
                      <td className="py-1.5">{EVENT_LABEL[e.type] ?? e.type}</td>
                      <td className="py-1.5 text-right font-mono">{e.total.toLocaleString()}</td>
                      <td className="py-1.5 text-right font-mono">{e.count_30d}</td>
                      <td className="py-1.5 text-right font-mono text-xs text-text3">{e.last_at ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* 최근 활동 타임라인 */}
          <div className="bg-surface border border-border rounded-2xl p-5 mt-5">
            <h2 className="text-sm font-bold mb-3 flex items-center gap-1.5"><Calendar size={14} className="text-primary" />{c.recent}</h2>
            {data.recent_events.length === 0 ? (
              <p className="text-xs text-text3">{c.none}</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {data.recent_events.map((r, i) => (
                  <span key={i} className="inline-flex items-center gap-1.5 bg-bg2 border border-border rounded-full px-2.5 py-1 text-xs">
                    <span>{EVENT_LABEL[r.type] ?? r.type}</span>
                    <span className="font-mono text-text3">{r.date}</span>
                  </span>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
