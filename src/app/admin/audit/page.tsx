"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useQuery } from "@tanstack/react-query";
import { adminApi } from "@/lib/api/endpoints/admin";
import type { AuditRow } from "@/types/api.types";

const ACTION_CLS: Record<string, string> = {
  CREATE: "bg-green-soft text-success border-success/30",
  UPDATE: "bg-amber-soft text-warning border-warning/40",
  DELETE: "bg-red-soft text-danger border-danger/40",
};

export default function AdminAuditPage() {
  const t = useTranslations("admin");
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ["admin", "audit", page],
    queryFn: () => adminApi.auditLog({ page, per_page: 30 }),
  });

  const rows = data?.items ?? [];
  const meta = data?.meta;

  return (
    <div className="p-7 max-w-5xl">
      <header className="mb-5">
        <h1 className="text-[22px] font-extrabold tracking-tight">{t("auditTitle")}</h1>
        <p className="text-xs text-text3 mt-0.5">{t("auditSubtitle")}</p>
      </header>

      {isLoading ? (
        <div className="py-12 text-center text-text3 text-sm">…</div>
      ) : rows.length === 0 ? (
        <div className="border border-border rounded-2xl py-14 text-center text-text3 text-sm">{t("auditEmpty")}</div>
      ) : (
        <div className="bg-surface border border-border rounded-2xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-bg2 text-text3 text-[11px] uppercase tracking-wide">
                <th className="text-left px-4 py-2.5 font-bold">{t("auditColWhen")}</th>
                <th className="text-left px-4 py-2.5 font-bold">{t("auditColActor")}</th>
                <th className="text-left px-4 py-2.5 font-bold">{t("auditColAction")}</th>
                <th className="text-left px-4 py-2.5 font-bold">{t("auditColEntity")}</th>
                <th className="text-left px-4 py-2.5 font-bold">{t("auditColChange")}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((a: AuditRow) => (
                <tr key={a.id} className="border-t border-border align-top">
                  <td className="px-4 py-2.5 text-text3 text-xs font-mono whitespace-nowrap">{a.created_at?.slice(0, 16).replace("T", " ")}</td>
                  <td className="px-4 py-2.5 text-text2 text-xs">{a.actor_name ?? "—"}</td>
                  <td className="px-4 py-2.5">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${ACTION_CLS[a.action] ?? "bg-bg2 text-text3 border-border"}`}>{a.action}</span>
                  </td>
                  <td className="px-4 py-2.5 text-text3 text-xs font-mono">{a.entity_type}</td>
                  <td className="px-4 py-2.5 text-text3 text-[11px] font-mono max-w-[260px] truncate">
                    {a.new_value ? JSON.stringify(a.new_value) : a.old_value ? JSON.stringify(a.old_value) : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {meta && meta.pages > 1 && (
        <div className="flex items-center justify-center gap-3 mt-4 text-xs">
          <button disabled={page === 1} onClick={() => setPage((p) => p - 1)} className="px-3 py-1.5 rounded-lg border border-border disabled:opacity-40">{t("prev")}</button>
          <span className="text-text3 font-mono">{page} / {meta.pages}</span>
          <button disabled={page >= meta.pages} onClick={() => setPage((p) => p + 1)} className="px-3 py-1.5 rounded-lg border border-border disabled:opacity-40">{t("next")}</button>
        </div>
      )}
    </div>
  );
}
