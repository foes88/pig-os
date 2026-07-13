"use client";

import { useQuery } from "@tanstack/react-query";
import { useLocale } from "next-intl";
import { useRouter } from "next/navigation";
import { Activity, AlertTriangle, CircleDashed, PauseCircle, CheckCircle2 } from "lucide-react";
import { adminApi } from "@/lib/api/endpoints/admin";
import type { DataMonitorRow } from "@/types/api.types";

// 운영자 — 농장별 데이터 입력 현황(Farm Data Monitor).
// 자족적 다국어(admin 콘솔은 운영자용 — 새 메시지 키 없이 인라인 7개어).
const T: Record<string, {
  title: string; sub: string; farm: string; country: string; sows: string;
  last: string; e7: string; e30: string; status: string; never: string; empty: string;
  onboarding: string; active: string; idle: string; stale: string; issues?: string;
}> = {
  en: { title: "Farm Data Monitor", sub: "Which farms are entering data — and which have gone quiet.", farm: "Farm", country: "Country", sows: "Sows", last: "Last entry", e7: "7d", e30: "30d", status: "Status", never: "never", empty: "No active farms yet.", onboarding: "Onboarding", active: "Active", idle: "Idle", stale: "Stale", issues: "Issues" },
  ko: { title: "농장 데이터 모니터", sub: "어느 농장이 데이터를 입력하고, 어느 농장이 조용한지.", farm: "농장", country: "국가", sows: "모돈", last: "마지막 입력", e7: "7일", e30: "30일", status: "상태", never: "없음", empty: "활성 농장이 아직 없습니다.", onboarding: "온보딩", active: "활성", idle: "휴면", stale: "방치", issues: "이슈" },
  zh: { title: "农场数据监控", sub: "哪些农场在录入数据，哪些已沉寂。", farm: "农场", country: "国家", sows: "母猪", last: "最后录入", e7: "7天", e30: "30天", status: "状态", never: "无", empty: "暂无活跃农场。", onboarding: "引导中", active: "活跃", idle: "闲置", stale: "沉寂", issues: "问题" },
  es: { title: "Monitor de datos de granjas", sub: "Qué granjas registran datos y cuáles se han quedado en silencio.", farm: "Granja", country: "País", sows: "Cerdas", last: "Último registro", e7: "7d", e30: "30d", status: "Estado", never: "nunca", empty: "Aún no hay granjas activas.", onboarding: "Iniciando", active: "Activa", idle: "Inactiva", stale: "Abandonada", issues: "Problemas" },
  vi: { title: "Giám sát dữ liệu trang trại", sub: "Trang trại nào đang nhập dữ liệu và trang trại nào đã im lặng.", farm: "Trang trại", country: "Quốc gia", sows: "Nái", last: "Nhập gần nhất", e7: "7n", e30: "30n", status: "Trạng thái", never: "chưa", empty: "Chưa có trang trại hoạt động.", onboarding: "Bắt đầu", active: "Hoạt động", idle: "Nghỉ", stale: "Bỏ trống", issues: "Lỗi" },
  th: { title: "มอนิเตอร์ข้อมูลฟาร์ม", sub: "ฟาร์มไหนกำลังบันทึกข้อมูล และฟาร์มไหนเงียบไป", farm: "ฟาร์ม", country: "ประเทศ", sows: "แม่สุกร", last: "บันทึกล่าสุด", e7: "7 วัน", e30: "30 วัน", status: "สถานะ", never: "ไม่มี", empty: "ยังไม่มีฟาร์มที่ใช้งาน", onboarding: "เริ่มต้น", active: "ใช้งาน", idle: "ว่าง", stale: "ทิ้งร้าง", issues: "ปัญหา" },
  pt: { title: "Monitor de dados das granjas", sub: "Quais granjas estão inserindo dados e quais ficaram em silêncio.", farm: "Granja", country: "País", sows: "Matrizes", last: "Último registro", e7: "7d", e30: "30d", status: "Status", never: "nunca", empty: "Ainda não há granjas ativas.", onboarding: "Integrando", active: "Ativa", idle: "Ociosa", stale: "Abandonada", issues: "Problemas" },
  ru: { title: "Монитор данных ферм", sub: "Какие фермы вводят данные, а какие затихли.", farm: "Ферма", country: "Страна", sows: "Свиноматки", last: "Последний ввод", e7: "7д", e30: "30д", status: "Статус", never: "нет", empty: "Пока нет активных ферм.", onboarding: "Онбординг", active: "Активна", idle: "Простой", stale: "Заброшена", issues: "Проблемы" },
};

const STATUS_META: Record<DataMonitorRow["status"], { cls: string; icon: typeof Activity }> = {
  active: { cls: "bg-green-soft text-success border-success/30", icon: CheckCircle2 },
  idle: { cls: "bg-amber-soft text-warning border-warning/40", icon: PauseCircle },
  stale: { cls: "bg-red-soft text-danger border-danger/40", icon: AlertTriangle },
  onboarding: { cls: "bg-primary-soft text-primary border-primary/30", icon: CircleDashed },
};

export default function DataMonitorPage() {
  const locale = useLocale();
  const router = useRouter();
  const c = T[locale] ?? T.en;
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
          <h1 className="text-[22px] font-extrabold tracking-tight">{c.title}</h1>
          <p className="text-xs text-text3 mt-0.5">{c.sub}</p>
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
                <span className="text-[11px] font-bold uppercase tracking-wide text-text3">{c[s]}</span>
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
                  <th className="text-left px-4 py-2.5 font-bold">{c.farm}</th>
                  <th className="text-left px-4 py-2.5 font-bold">{c.country}</th>
                  <th className="text-right px-4 py-2.5 font-bold">{c.sows}</th>
                  <th className="text-left px-4 py-2.5 font-bold">{c.last}</th>
                  <th className="text-right px-4 py-2.5 font-bold">{c.e7}</th>
                  <th className="text-right px-4 py-2.5 font-bold">{c.e30}</th>
                  <th className="text-right px-4 py-2.5 font-bold">{c.issues ?? "Issues"}</th>
                  <th className="text-left px-4 py-2.5 font-bold">{c.status}</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr><td colSpan={8} className="px-4 py-10 text-center text-text3">…</td></tr>
                ) : data.length === 0 ? (
                  <tr><td colSpan={8} className="px-4 py-10 text-center text-text3">{c.empty}</td></tr>
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
                        {r.last_event_at ? r.last_event_at.slice(0, 10) : c.never}
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
                          <m.icon size={11} />{c[r.status]}
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
