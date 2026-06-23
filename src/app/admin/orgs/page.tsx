"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useQuery } from "@tanstack/react-query";
import { ChevronRight, ChevronDown, Building2, Tractor } from "lucide-react";
import { adminApi } from "@/lib/api/endpoints/admin";
import type { AdminOrgRow, AdminOrgFarm } from "@/types/api.types";

// org_type → 라벨키 + 색
const TYPE_META: Record<string, { key: string; cls: string }> = {
  VENDOR: { key: "orgVendor", cls: "bg-console text-white border-console" },
  DISTRIBUTOR: { key: "orgDistributor", cls: "bg-green-soft text-success border-success/30" },
  DEALER: { key: "orgDealer", cls: "bg-amber-soft text-warning border-warning/40" },
  INDEPENDENT: { key: "orgIndependent", cls: "bg-bg2 text-text2 border-border" },
};

export default function AdminOrgsPage() {
  const t = useTranslations("admin");
  const { data, isLoading } = useQuery({ queryKey: ["admin", "orgs"], queryFn: () => adminApi.orgs() });

  const orgs = data ?? [];
  const childrenOf = (id: string | null) => orgs.filter((o) => o.parent_org_id === id);
  const roots = childrenOf(null);

  return (
    <div className="p-7 max-w-4xl">
      <header className="mb-5">
        <h1 className="text-[22px] font-extrabold tracking-tight">{t("orgsTitle")}</h1>
        <p className="text-xs text-text3 mt-0.5">{t("orgsSubtitle")}</p>
      </header>

      {isLoading ? (
        <div className="py-12 text-center text-text3 text-sm">…</div>
      ) : roots.length === 0 ? (
        <div className="border border-border rounded-2xl py-14 text-center text-text3 text-sm">{t("orgsEmpty")}</div>
      ) : (
        <div className="bg-surface border border-border rounded-2xl p-2">
          {roots.map((o) => <OrgNode key={o.id} org={o} childrenOf={childrenOf} depth={0} t={t} />)}
        </div>
      )}
    </div>
  );
}

function OrgNode({
  org, childrenOf, depth, t,
}: {
  org: AdminOrgRow;
  childrenOf: (id: string | null) => AdminOrgRow[];
  depth: number;
  t: (k: string, v?: Record<string, string | number>) => string;
}) {
  const [open, setOpen] = useState(depth === 0);
  const [showFarms, setShowFarms] = useState(false);
  const kids = childrenOf(org.id);
  const meta = TYPE_META[org.org_type] ?? TYPE_META.INDEPENDENT;
  const expandable = kids.length > 0 || org.farm_count > 0;

  const { data: farms } = useQuery({
    queryKey: ["admin", "orgFarms", org.id],
    queryFn: () => adminApi.orgFarms(org.id),
    enabled: showFarms,
  });

  return (
    <div>
      <div
        className="flex items-center gap-2 px-2 py-2 rounded-lg hover:bg-bg2 transition"
        style={{ paddingLeft: depth * 20 + 8 }}
      >
        <button
          onClick={() => setOpen((v) => !v)}
          className={`w-5 h-5 flex items-center justify-center text-text3 ${expandable ? "" : "invisible"}`}
        >
          {open ? <ChevronDown size={15} /> : <ChevronRight size={15} />}
        </button>
        <Building2 size={15} className="text-text3 shrink-0" />
        <span className="font-semibold text-text text-sm">{org.name}</span>
        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${meta.cls}`}>{t(meta.key)}</span>
        <span className="text-[11px] text-text3 font-mono ml-auto">
          {t("orgFarmCount", { n: org.farm_count })} · {t("orgUserCount", { n: org.user_count })}
        </span>
      </div>

      {open && (
        <div>
          {kids.map((k) => <OrgNode key={k.id} org={k} childrenOf={childrenOf} depth={depth + 1} t={t} />)}
          {org.farm_count > 0 && (
            <div style={{ paddingLeft: (depth + 1) * 20 + 8 }}>
              <button
                onClick={() => setShowFarms((v) => !v)}
                className="flex items-center gap-1.5 px-2 py-1.5 text-xs text-primary font-semibold hover:underline"
              >
                <Tractor size={13} /> {showFarms ? t("orgHideFarms") : t("orgShowFarms", { n: org.farm_count })}
              </button>
              {showFarms && (farms ?? []).map((f: AdminOrgFarm) => (
                <div key={f.id} className="flex items-center gap-2 px-2 py-1.5 text-xs text-text2" style={{ paddingLeft: 24 }}>
                  <Tractor size={12} className="text-text3" />
                  <span className="font-medium">{f.name}</span>
                  <span className="text-text3 font-mono">{f.farm_code}</span>
                  {!f.active && <span className="text-[10px] text-text3">({t("inactive")})</span>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
