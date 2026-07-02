"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, RotateCcw, Globe, Flag, Building2 } from "lucide-react";
import { thresholdsApi } from "@/lib/api/endpoints/thresholds";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";
import type { ThresholdRow } from "@/types/api.types";

const SCOPE_META: Record<string, { icon: typeof Globe; cls: string }> = {
  farm:    { icon: Building2, cls: "text-primary border-primary/30 bg-primary/5" },
  country: { icon: Flag,      cls: "text-success border-success/30 bg-green-soft" },
  global:  { icon: Globe,     cls: "text-success border-success/30 bg-green-soft" },
};
const CONF_CLS: Record<string, string> = {
  high: "text-success", medium: "text-warning", low: "text-danger",
};

export default function ThresholdsPage() {
  const t = useTranslations("thresholds");
  const farmId = useAuthStore((s) => s.activeFarmId);
  const qc = useQueryClient();
  const [editing, setEditing] = useState<ThresholdRow | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: queryKeys.thresholds.list(farmId ?? ""),
    queryFn: () => thresholdsApi.list(farmId!),
    enabled: !!farmId,
  });

  const invalidate = () => qc.invalidateQueries({ queryKey: queryKeys.thresholds.list(farmId ?? "") });

  const reset = useMutation({
    mutationFn: (code: string) => thresholdsApi.clearOverride(farmId!, code),
    onSuccess: invalidate,
  });

  if (!farmId) return <div className="p-7 text-text3">{t("selectFarm")}</div>;

  const rows = (data ?? []).filter((r) => r.warning != null || r.critical != null);

  return (
    <div className="p-7 max-w-4xl">
      <div className="mb-5">
        <h1 className="text-[22px] font-extrabold tracking-tight">{t("title")}</h1>
        <p className="text-xs text-text3 mt-1">{t("subtitle")}</p>
      </div>

      {isLoading && <div className="text-text3 py-10 text-center">{t("loading")}</div>}

      {data && (
        <div className="bg-surface border border-border rounded-2xl overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-background text-text3 text-[11px] uppercase">
              <tr>
                <th className="text-left px-4 py-2.5 font-semibold">{t("metric")}</th>
                <th className="text-right px-3 py-2.5 font-semibold">{t("warning")}</th>
                <th className="text-right px-3 py-2.5 font-semibold">{t("critical")}</th>
                <th className="text-left px-3 py-2.5 font-semibold">{t("scope")}</th>
                <th className="text-left px-3 py-2.5 font-semibold">{t("sourceCol")}</th>
                <th className="px-3 py-2.5"></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => {
                const sm = SCOPE_META[r.scope] ?? SCOPE_META.global;
                const ScopeIcon = sm.icon;
                return (
                  <tr key={r.metric_code} className="border-t border-border">
                    <td className="px-4 py-2.5">
                      <span className="font-semibold">{t.has(`m.${r.metric_code}`) ? t(`m.${r.metric_code}`) : r.metric_code}</span>
                      <span className="text-[10px] text-text3 ml-1.5">{r.direction === "above" ? "↑" : "↓"} {r.unit}</span>
                    </td>
                    <td className="px-3 py-2.5 text-right font-mono text-warning">{r.warning ?? "-"}</td>
                    <td className="px-3 py-2.5 text-right font-mono text-danger">{r.critical ?? "-"}</td>
                    <td className="px-3 py-2.5">
                      <span className={`inline-flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full border ${sm.cls}`}>
                        <ScopeIcon className="w-2.5 h-2.5" /> {t(`scopeVal.${r.scope}`)}
                      </span>
                    </td>
                    <td className="px-3 py-2.5">
                      <div className="text-[11px] text-text3 max-w-[160px] truncate" title={r.source ?? ""}>{r.source ?? "-"}</div>
                      {r.confidence && <span className={`text-[9px] font-bold ${CONF_CLS[r.confidence]}`}>{t(`conf.${r.confidence}`)}{r.is_proxy ? " · " + t("proxy") : ""}</span>}
                    </td>
                    <td className="px-3 py-2.5 text-right whitespace-nowrap">
                      <button onClick={() => setEditing(r)} title={t("edit")} className="p-1 rounded text-text3 hover:text-primary hover:bg-primary/5">
                        <Pencil className="w-3.5 h-3.5" />
                      </button>
                      {r.is_override && (
                        <button onClick={() => reset.mutate(r.metric_code)} title={t("reset")} className="p-1 rounded text-text3 hover:text-danger hover:bg-red-soft">
                          <RotateCcw className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      <p className="text-[11px] text-text3 mt-3">{t("note")}</p>

      {editing && (
        <EditModal farmId={farmId} row={editing} onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); invalidate(); }} />
      )}
    </div>
  );
}

function EditModal({ farmId, row, onClose, onSaved }: { farmId: string; row: ThresholdRow; onClose: () => void; onSaved: () => void }) {
  const t = useTranslations("thresholds");
  const [warning, setWarning] = useState(row.warning?.toString() ?? "");
  const [critical, setCritical] = useState(row.critical?.toString() ?? "");
  const [error, setError] = useState<string | null>(null);

  const save = useMutation({
    mutationFn: () => thresholdsApi.setOverride(farmId, row.metric_code, {
      warning: warning === "" ? null : Number(warning),
      critical: critical === "" ? null : Number(critical),
    }),
    onSuccess: onSaved,
    onError: () => setError(t("saveError")),
  });

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-background border border-border rounded-2xl w-full max-w-sm p-5" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-base font-bold mb-1">{t.has(`m.${row.metric_code}`) ? t(`m.${row.metric_code}`) : row.metric_code}</h2>
        <p className="text-[11px] text-text3 mb-4">{t("editHint", { dir: row.direction === "above" ? "↑" : "↓", unit: row.unit })}</p>
        <div className="space-y-3">
          <label className="block">
            <span className="text-[11px] font-medium text-text3 mb-1 block">{t("warning")}</span>
            <input type="number" step="0.1" value={warning} onChange={(e) => setWarning(e.target.value)}
              className="w-full border border-border rounded-lg px-2.5 py-1.5 text-sm bg-surface" />
          </label>
          <label className="block">
            <span className="text-[11px] font-medium text-text3 mb-1 block">{t("critical")}</span>
            <input type="number" step="0.1" value={critical} onChange={(e) => setCritical(e.target.value)}
              className="w-full border border-border rounded-lg px-2.5 py-1.5 text-sm bg-surface" />
          </label>
        </div>
        {error && <p className="text-xs text-danger mt-3">{error}</p>}
        <div className="flex gap-2 mt-5">
          <button onClick={onClose} className="flex-1 text-sm border border-border rounded-lg py-2 hover:bg-border">{t("cancel")}</button>
          <button onClick={() => save.mutate()} disabled={save.isPending}
            className="flex-1 text-sm font-medium text-white bg-primary rounded-lg py-2 hover:opacity-90 disabled:opacity-50">
            {save.isPending ? t("saving") : t("save")}
          </button>
        </div>
      </div>
    </div>
  );
}
