"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { localToday } from "@/lib/date";
import { feedApi, type CreateFeedRecordRequest } from "@/lib/api/endpoints/feed";
import { useAuthStore } from "@/store/auth.store";
import { canEntry } from "@/lib/auth/permissions";

export default function FeedPage() {
  const t = useTranslations("feed");
  const farmId = useAuthStore((s) => s.activeFarmId);
  const canWrite = canEntry(useAuthStore((s) => s.user?.role));
  const queryClient = useQueryClient();

  const [recordDate, setRecordDate] = useState(localToday());
  const [feedType, setFeedType] = useState("");
  const [quantityKg, setQuantityKg] = useState("");
  const [err, setErr] = useState<string | null>(null);

  const { data: records = [], isLoading } = useQuery({
    queryKey: ["feed", farmId],
    queryFn: () => feedApi.list(farmId!),
    enabled: !!farmId,
  });

  const createMut = useMutation({
    mutationFn: (body: CreateFeedRecordRequest) => feedApi.create(farmId!, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["feed", farmId] });
      setQuantityKg("");
      setFeedType("");
      setErr(null);
    },
    onError: () => setErr(t("saveError")),
  });

  const delMut = useMutation({
    mutationFn: (id: string) => feedApi.delete(farmId!, id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["feed", farmId] }),
  });

  if (!farmId) {
    return <div className="p-6 text-text3">{t("noFarm")}</div>;
  }

  function submit() {
    const q = parseFloat(quantityKg);
    if (!q || q <= 0) {
      setErr(t("qtyError"));
      return;
    }
    createMut.mutate({
      record_date: recordDate,
      quantity_kg: q,
      feed_type: feedType.trim() || null,
    });
  }

  return (
    <div className="ml-[220px] max-md:ml-0 p-6 max-w-3xl">
      <h1 className="text-2xl font-extrabold text-text">{t("title")}</h1>
      <p className="text-sm text-text3 mt-1">{t("subtitle")}</p>

      {canWrite && (
        <div className="mt-6 rounded-2xl border border-border bg-surface p-5">
          <div className="text-sm font-bold text-text mb-3">{t("add")}</div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <label className="block">
              <span className="text-xs text-text3">{t("recordDate")}</span>
              <input type="date" value={recordDate} onChange={(e) => setRecordDate(e.target.value)}
                     className="mt-1 w-full rounded-lg border border-border bg-bg px-3 py-2 text-sm" />
            </label>
            <label className="block">
              <span className="text-xs text-text3">{t("feedType")}</span>
              <input type="text" value={feedType} onChange={(e) => setFeedType(e.target.value)}
                     placeholder={t("feedTypePlaceholder")}
                     className="mt-1 w-full rounded-lg border border-border bg-bg px-3 py-2 text-sm" />
            </label>
            <label className="block">
              <span className="text-xs text-text3">{t("quantityKg")}</span>
              <input type="number" min="0" step="0.1" value={quantityKg}
                     onChange={(e) => setQuantityKg(e.target.value)}
                     className="mt-1 w-full rounded-lg border border-border bg-bg px-3 py-2 text-sm font-mono" />
            </label>
          </div>
          {err && <div className="mt-2 text-xs text-danger">{err}</div>}
          <button onClick={submit} disabled={createMut.isPending}
                  className="mt-4 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white disabled:opacity-50">
            {createMut.isPending ? t("saving") : t("save")}
          </button>
        </div>
      )}

      <div className="mt-6">
        <div className="text-sm font-bold text-text mb-2">{t("recent")}</div>
        {isLoading ? (
          <div className="text-text3 text-sm">…</div>
        ) : records.length === 0 ? (
          <div className="rounded-xl border border-dashed border-border p-6 text-center text-text3 text-sm">
            {t("empty")}
          </div>
        ) : (
          <div className="rounded-2xl border border-border overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-bg2 text-text3 text-xs">
                <tr>
                  <th className="text-left px-4 py-2">{t("recordDate")}</th>
                  <th className="text-left px-4 py-2">{t("feedType")}</th>
                  <th className="text-right px-4 py-2">{t("quantityKg")}</th>
                  {canWrite && <th className="px-4 py-2" />}
                </tr>
              </thead>
              <tbody>
                {records.map((r) => (
                  <tr key={r.id} className="border-t border-border">
                    <td className="px-4 py-2 font-mono">{r.record_date}</td>
                    <td className="px-4 py-2">{r.feed_type ?? "—"}</td>
                    <td className="px-4 py-2 text-right font-mono">{r.quantity_kg}</td>
                    {canWrite && (
                      <td className="px-4 py-2 text-right">
                        <button onClick={() => delMut.mutate(r.id)}
                                className="text-xs text-danger hover:underline">{t("delete")}</button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
