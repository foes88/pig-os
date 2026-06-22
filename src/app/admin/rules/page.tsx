"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { adminApi } from "@/lib/api/endpoints/admin";
import type { AdminRuleRow } from "@/types/api.types";

export default function AdminRulesPage() {
  const t = useTranslations("admin");
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["admin", "rules"], queryFn: () => adminApi.rules() });

  const mut = useMutation({
    mutationFn: ({ id, body }: { id: string; body: { enabled?: boolean; warning?: number | null; critical?: number | null } }) =>
      adminApi.updateRule(id, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "rules"] }),
  });

  const rows = data ?? [];

  return (
    <div className="p-7 max-w-5xl">
      <header className="mb-5">
        <h1 className="text-[22px] font-extrabold tracking-tight">{t("rulesTitle")}</h1>
        <p className="text-xs text-text3 mt-0.5">{t("rulesSubtitle")}</p>
      </header>

      {isLoading ? (
        <div className="py-12 text-center text-text3 text-sm">…</div>
      ) : (
        <div className="bg-surface border border-border rounded-2xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-bg2 text-text3 text-[11px] uppercase tracking-wide">
                <th className="text-left px-4 py-2.5 font-bold">{t("ruleColRule")}</th>
                <th className="text-left px-4 py-2.5 font-bold">{t("ruleColDomain")}</th>
                <th className="text-right px-4 py-2.5 font-bold">{t("ruleColWarning")}</th>
                <th className="text-right px-4 py-2.5 font-bold">{t("ruleColCritical")}</th>
                <th className="text-center px-4 py-2.5 font-bold">{t("ruleColEnabled")}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => <RuleRow key={r.rule_id} r={r} t={t} onSave={(body) => mut.mutate({ id: r.rule_id, body })} />)}
            </tbody>
          </table>
        </div>
      )}
      <p className="text-xs text-text3 mt-4">{t("rulesNote")}</p>
    </div>
  );
}

function RuleRow({
  r, t, onSave,
}: {
  r: AdminRuleRow;
  t: (k: string) => string;
  onSave: (body: { enabled?: boolean; warning?: number | null; critical?: number | null }) => void;
}) {
  const [w, setW] = useState(r.warning?.toString() ?? "");
  const [c, setC] = useState(r.critical?.toString() ?? "");
  const dirty = (w !== (r.warning?.toString() ?? "")) || (c !== (r.critical?.toString() ?? ""));

  return (
    <tr className={`border-t border-border ${!r.enabled ? "opacity-50" : ""}`}>
      <td className="px-4 py-2.5">
        <div className="font-mono text-xs font-bold text-text">{r.rule_id}</div>
        <div className="text-[11px] text-text3">{r.description}</div>
      </td>
      <td className="px-4 py-2.5 text-text3 text-xs font-mono">{r.domain}</td>
      <td className="px-4 py-2.5 text-right">
        <input value={w} onChange={(e) => setW(e.target.value)} type="number" placeholder="—"
          className="w-16 px-2 py-1 rounded border border-border bg-bg2 text-xs font-mono text-right outline-none focus:border-primary" />
      </td>
      <td className="px-4 py-2.5 text-right">
        <input value={c} onChange={(e) => setC(e.target.value)} type="number" placeholder="—"
          className="w-16 px-2 py-1 rounded border border-border bg-bg2 text-xs font-mono text-right outline-none focus:border-primary" />
        {dirty && (
          <button onClick={() => onSave({ warning: w === "" ? null : Number(w), critical: c === "" ? null : Number(c) })}
            className="ml-2 text-[11px] font-semibold text-white bg-primary px-2 py-1 rounded">{t("ruleSave")}</button>
        )}
      </td>
      <td className="px-4 py-2.5 text-center">
        <button onClick={() => onSave({ enabled: !r.enabled })}
          className={`text-[10px] font-bold px-2.5 py-1 rounded-full border ${r.enabled ? "bg-green-soft text-success border-success/30" : "bg-bg2 text-text3 border-border"}`}>
          {r.enabled ? t("ruleOn") : t("ruleOff")}
        </button>
      </td>
    </tr>
  );
}
