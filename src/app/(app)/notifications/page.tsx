"use client";

import { useState } from "react";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { kpiApi } from "@/lib/api/endpoints/kpi";
import { notificationsApi } from "@/lib/api/endpoints/notifications";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";
import { AlertsTabs } from "@/components/AlertsTabs";
import type { Alert, NotificationItem } from "@/types/api.types";

const PAGE_SIZE = 20;

// 색상만 보관, 라벨은 notifications.sevXxx 키
const SEVERITY_STYLES: Record<Alert["severity"], { bg: string; dot: string; key: string }> = {
  CRITICAL: { bg: "bg-red-50 border-red-200",   dot: "bg-danger",   key: "sevCritical" },
  WARNING:  { bg: "bg-amber-50 border-amber-200", dot: "bg-warning",  key: "sevWarning" },
  INFO:     { bg: "bg-green-soft border-success/30",   dot: "bg-primary",  key: "sevInfo" },
  OK:       { bg: "bg-surface border-border",     dot: "bg-success",  key: "sevOk" },
};

const SEV_DOT: Record<string, string> = {
  CRITICAL: "bg-danger", WARNING: "bg-warning", INFO: "bg-primary",
};

function targetHref(n: NotificationItem): string | null {
  if (n.related_entity_type === "sow" && n.related_entity_id) return `/sows/${n.related_entity_id}`;
  return null;
}

export default function NotificationsPage() {
  const t = useTranslations("notifications");
  const router = useRouter();
  const qc = useQueryClient();
  const farmId = useAuthStore((s) => s.activeFarmId);

  const [filter, setFilter] = useState<"ALL" | "CRITICAL" | "WARNING" | "INFO">("ALL");
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [limit, setLimit] = useState(PAGE_SIZE);

  // 실시간 KPI 알림 (대시보드 Rule Engine)
  const { data: dashboard, isLoading } = useQuery({
    queryKey: queryKeys.kpi.dashboard(farmId ?? ""),
    queryFn: () => kpiApi.dashboard(farmId!),
    enabled: !!farmId,
  });

  // 영구 인앱 알림 (P12-6)
  const { data: notif, isLoading: notifLoading } = useQuery({
    queryKey: [...queryKeys.notifications.list(farmId ?? "", unreadOnly), limit],
    queryFn: () => notificationsApi.list({ farmId: farmId!, unreadOnly, limit, offset: 0 }),
    enabled: !!farmId,
  });

  const invalidateNotif = () => {
    qc.invalidateQueries({ queryKey: ["notifications"] });
  };

  const markRead = useMutation({
    mutationFn: (id: string) => notificationsApi.markRead(id),
    onSuccess: invalidateNotif,
  });
  const markAll = useMutation({
    mutationFn: () => notificationsApi.markAllRead(farmId ?? undefined),
    onSuccess: invalidateNotif,
  });

  const alerts = dashboard?.alerts ?? [];
  const active = alerts.filter((a) => a.severity !== "OK");
  const filtered = filter === "ALL" ? active : active.filter((a) => a.severity === filter);

  const items = notif?.items ?? [];
  const unreadCount = notif?.unread_count ?? 0;
  const total = notif?.total ?? 0;

  const handleClick = (n: NotificationItem) => {
    if (!n.read_at) markRead.mutate(n.id);
    const href = targetHref(n);
    if (href) router.push(href);
  };

  if (!farmId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-text3">{t("selectFarm")}</p>
      </div>
    );
  }

  return (
    <div className="p-7 max-w-2xl">
      <AlertsTabs />
      {/* Header */}
      <div className="mb-6 flex items-start justify-between gap-3">
        <div>
          <h1 className="text-[22px] font-extrabold tracking-tight">{t("title")}</h1>
          <p className="text-xs text-text3 mt-0.5">{t("subtitle")}</p>
        </div>
        {unreadCount > 0 && (
          <button
            onClick={() => markAll.mutate()}
            disabled={markAll.isPending}
            className="text-xs font-semibold rounded-full px-3 py-1.5 border border-border text-text3 hover:border-primary transition disabled:opacity-50"
          >
            {t("markAllRead")}
          </button>
        )}
      </div>

      {/* ── 실시간 KPI 알림 ───────────────────────────────────────── */}
      <section className="mb-8">
        <div className="text-[11px] font-bold text-faint uppercase tracking-widest mb-2">
          {t("realtimeSection")}
        </div>

        {isLoading && (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-border rounded-2xl animate-pulse" />
            ))}
          </div>
        )}

        {!isLoading && active.length === 0 && (
          <p className="text-xs text-text3 py-3">{t("realtimeEmpty")}</p>
        )}

        {active.length > 0 && (
          <>
            <div className="flex gap-1.5 mb-3">
              {(["ALL", "CRITICAL", "WARNING", "INFO"] as const).map((sev) => {
                const count = sev === "ALL" ? active.length : active.filter((a) => a.severity === sev).length;
                const labels: Record<string, string> = {
                  ALL: t("filterAll"), CRITICAL: t("sevCritical"), WARNING: t("sevWarning"), INFO: t("sevInfo"),
                };
                return (
                  <button
                    key={sev}
                    onClick={() => setFilter(sev)}
                    className={`text-xs font-semibold rounded-full px-3 py-1.5 border transition ${
                      filter === sev ? "bg-primary text-white border-primary" : "border-border text-text3 hover:border-primary"
                    }`}
                  >
                    {labels[sev]} {count}
                  </button>
                );
              })}
            </div>
            <div className="space-y-2">
              {filtered.map((alert) => {
                const s = SEVERITY_STYLES[alert.severity];
                return (
                  <div key={alert.rule_id} className={`border rounded-2xl px-4 py-3.5 ${s.bg}`}>
                    <div className="flex items-start gap-3">
                      <span className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${s.dot}`} />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-0.5">
                          <span className="text-[10px] font-bold uppercase tracking-wide text-text3">{alert.kpi}</span>
                          <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded bg-white/70 text-text3">{t(s.key)}</span>
                        </div>
                        <p className="text-sm font-semibold text-text leading-snug">{alert.message}</p>
                        {alert.current_value != null && alert.target_value != null && (
                          <p className="text-xs text-text3 mt-0.5 font-mono">
                            {t("currentTarget", { cur: alert.current_value.toFixed(2), tgt: alert.target_value.toFixed(2) })}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </section>

      {/* ── 영구 알림 (P12-6) ─────────────────────────────────────── */}
      <section>
        <div className="flex items-center justify-between mb-2">
          <div className="text-[11px] font-bold text-faint uppercase tracking-widest">
            {t("savedSection")}
            {unreadCount > 0 && (
              <span className="ml-2 text-primary">{t("unreadBadge", { n: unreadCount })}</span>
            )}
          </div>
          <button
            onClick={() => { setUnreadOnly((v) => !v); setLimit(PAGE_SIZE); }}
            className={`text-xs font-semibold rounded-full px-3 py-1 border transition ${
              unreadOnly ? "bg-primary text-white border-primary" : "border-border text-text3 hover:border-primary"
            }`}
          >
            {t("filterUnread")}
          </button>
        </div>

        {notifLoading && items.length === 0 && (
          <div className="space-y-2">
            {[1, 2].map((i) => <div key={i} className="h-14 bg-border rounded-2xl animate-pulse" />)}
          </div>
        )}

        {!notifLoading && items.length === 0 && (
          <p className="text-xs text-text3 py-6 text-center">{t("savedEmpty")}</p>
        )}

        <div className="space-y-2">
          {items.map((n) => {
            const href = targetHref(n);
            const clickable = href != null;
            return (
              <div
                key={n.id}
                onClick={() => clickable && handleClick(n)}
                className={`border rounded-2xl px-4 py-3 flex items-start gap-3 transition ${
                  n.read_at ? "border-border bg-surface" : "border-primary/30 bg-green-soft/40"
                } ${clickable ? "cursor-pointer hover:border-primary" : ""}`}
              >
                <span className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${n.severity ? (SEV_DOT[n.severity] ?? "bg-text3") : "bg-text3"}`} />
                <div className="flex-1 min-w-0">
                  <p className={`text-sm leading-snug ${n.read_at ? "text-text2" : "font-semibold text-text"}`}>{n.title}</p>
                  <p className="text-xs text-text3 mt-0.5 break-words">{n.body}</p>
                </div>
                {!n.read_at && (
                  <button
                    onClick={(e) => { e.stopPropagation(); markRead.mutate(n.id); }}
                    className="text-[11px] font-semibold text-primary hover:underline flex-shrink-0"
                  >
                    {t("markRead")}
                  </button>
                )}
              </div>
            );
          })}
        </div>

        {items.length < total && (
          <button
            onClick={() => setLimit((l) => l + PAGE_SIZE)}
            className="mt-3 w-full text-xs font-semibold rounded-2xl px-4 py-2.5 border border-border text-text3 hover:border-primary transition"
          >
            {t("loadMore")}
          </button>
        )}
      </section>
    </div>
  );
}
