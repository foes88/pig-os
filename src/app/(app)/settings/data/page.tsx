"use client";
import { useMemo } from "react";
import { useTranslations } from "next-intl";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ShieldCheck, Info } from "lucide-react";
import { consentApi } from "@/lib/api/endpoints/consent";
import { farmsApi } from "@/lib/api/endpoints/farms";
import { useAuthStore } from "@/store/auth.store";
import type { ConsentStatus, SignupPlan } from "@/types/api.types";

// 설정 → 데이터·프라이버시 (TERMS_DISPLAY §4 설정화면, §7 철회·제외 플로우).
// 현재 유효 동의 상태 + 목적별 철회/이의/제외요청. D-04 철회효과 고지.
const STATUS_CLS: Record<string, string> = {
  GRANTED: "bg-green-soft text-success border-success/30",
  NOTICE_GIVEN: "bg-bg2 text-text3 border-border",
  WITHDRAWN: "bg-red-soft text-danger border-danger/30",
  OBJECTED: "bg-amber-soft text-warning border-warning/30",
  EXCLUSION_REQUESTED: "bg-amber-soft text-warning border-warning/30",
};

// 목적별 철회 액션 (없으면 철회 불가 = 계약 이행 등)
const ACTION_FOR: Record<string, string | null> = {
  SERVICE_OPERATION: null,
  ANON_AGG_STATS: "EXCLUSION_REQUESTED",
  AI_MODEL_TRAINING: "WITHDRAWN",
  NAMED_RESEARCH: "WITHDRAWN",
  TRANSACTION_MATCHING: "WITHDRAWN",
  EXTERNAL_AI_PROCESSING: null,
};

export default function DataPrivacyPage() {
  const t = useTranslations("consent");
  const qc = useQueryClient();
  const activeFarmId = useAuthStore((s) => s.activeFarmId);

  const { data: farms } = useQuery({ queryKey: ["farms"], queryFn: () => farmsApi.list() });
  const farm = useMemo(
    () => farms?.find((f) => f.id === activeFarmId) ?? farms?.[0],
    [farms, activeFarmId],
  );

  const { data: current = [] } = useQuery({
    queryKey: ["consent", "current", activeFarmId],
    queryFn: () => consentApi.current(activeFarmId ?? undefined),
    enabled: !!activeFarmId,
  });

  const { data: plan } = useQuery<SignupPlan>({
    queryKey: ["consent", "plan", farm?.country],
    queryFn: () => consentApi.signupPlan({
      selected_country: farm!.country, farm_country: farm!.country, include_body: true,
    }),
    enabled: !!farm?.country,
  });

  const withdraw = useMutation({
    mutationFn: (args: { purpose_code: string; action: string }) =>
      consentApi.withdraw({ purpose_code: args.purpose_code, farm_id: activeFarmId, action: args.action }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["consent", "current", activeFarmId] }),
  });

  const byCode = useMemo(() => {
    const m: Record<string, ConsentStatus> = {};
    for (const c of current) m[c.purpose_code] = c;
    return m;
  }, [current]);

  const purposes = plan?.purposes.filter((p) => p.visible) ?? [];

  return (
    <div className="max-w-2xl mx-auto px-7 py-6">
      <div className="flex items-center gap-2 mb-1">
        <ShieldCheck size={20} className="text-primary" />
        <h1 className="text-xl font-extrabold tracking-tight text-text">{t("settingsTitle")}</h1>
      </div>
      <p className="text-[13px] text-text3 mb-5">{t("settingsSubtitle")}</p>

      {/* D-04 철회 효과 고지 */}
      <div className="flex items-start gap-2 bg-primary-soft/40 border border-primary/20 rounded-xl px-3 py-2.5 mb-5">
        <Info size={14} className="text-text2 mt-0.5 shrink-0" />
        <p className="text-xs text-text2 leading-relaxed">{t("withdrawEffectNotice")}</p>
      </div>

      {plan?.notice_version && (
        <p className="text-[11px] font-mono text-text3 mb-3">
          {t("documentsTitle")}: {plan.notice_version}
        </p>
      )}

      <div className="space-y-2">
        {purposes.map((p) => {
          const cur = byCode[p.purpose_code];
          const action = ACTION_FOR[p.purpose_code];
          const withdrawn = cur && ["WITHDRAWN", "OBJECTED", "EXCLUSION_REQUESTED"].includes(cur.consent_status);
          return (
            <div key={p.purpose_code} className="bg-surface border border-border rounded-xl px-4 py-3">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="text-sm font-semibold text-text">{t(`purpose.${p.purpose_code}.label`)}</div>
                  <p className="text-xs text-text3 mt-0.5 leading-relaxed">{t(`purpose.${p.purpose_code}.desc`)}</p>
                </div>
                {cur && (
                  <span className={`shrink-0 text-[10px] font-bold px-2 py-0.5 rounded-full border ${STATUS_CLS[cur.consent_status] ?? "bg-bg2 text-text3 border-border"}`}>
                    {t(`status.${cur.consent_status}`)}
                  </span>
                )}
              </div>
              {action && !withdrawn && (
                <button
                  onClick={() => withdraw.mutate({ purpose_code: p.purpose_code, action })}
                  disabled={withdraw.isPending}
                  className="mt-2 text-xs font-semibold text-danger border border-danger/30 rounded-lg px-3 py-1.5 hover:bg-red-soft disabled:opacity-50"
                >
                  {t(`action.${action}`)}
                </button>
              )}
              {!action && (
                <p className="mt-2 text-[11px] text-text3">{t("action.contractRequired")}</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
