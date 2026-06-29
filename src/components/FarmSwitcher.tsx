"use client";

import { useEffect } from "react";
import { Warehouse } from "lucide-react";
import { useQuery } from "@tanstack/react-query";

import { farmsApi } from "@/lib/api/endpoints/farms";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";

/**
 * 농장 전환기. 사용자가 접근 가능한 농장(총판/대리점은 하위 전체)을 나열하고
 * 활성 농장을 전환한다. 전환 시 농장-스코프 쿼리를 무효화해 새 농장 데이터로 갱신.
 * 접근 농장이 1개뿐이면 이름만 표시, 0개면 아무것도 렌더하지 않는다.
 */
export function FarmSwitcher() {
  const activeFarmId = useAuthStore((s) => s.activeFarmId);
  const setActiveFarmId = useAuthStore((s) => s.setActiveFarmId);

  const { data: farms = [] } = useQuery({
    queryKey: queryKeys.farms.all(),
    queryFn: () => farmsApi.list(),
  });

  // 활성 농장이 접근 목록에 없으면(초기/회수 후) 첫 농장으로 보정.
  useEffect(() => {
    if (farms.length === 0) return;
    if (!activeFarmId || !farms.some((f) => f.id === activeFarmId)) {
      setActiveFarmId(farms[0].id);
    }
  }, [farms, activeFarmId, setActiveFarmId]);

  if (farms.length === 0) return null;

  if (farms.length === 1) {
    return (
      <div className="flex items-center gap-1.5 text-text2 text-xs font-semibold max-w-[180px]">
        <Warehouse size={14} className="text-text3 shrink-0" />
        <span className="truncate">{farms[0].name}</span>
      </div>
    );
  }

  const onSwitch = (farmId: string) => {
    if (farmId === activeFarmId) return;
    setActiveFarmId(farmId);
    // 농장-스코프 쿼리는 key에 farmId가 포함돼 전환 시 자동 재조회되므로 전체 invalidate
    // (refetch storm: /me·/farms·알림까지)는 불필요. 혹시 모를 비-farm-key 쿼리 대비
    // farmId 미포함이지만 농장 의존인 쿼리는 없음(감사 확인).
  };

  return (
    <div className="flex items-center gap-1.5">
      <Warehouse size={14} className="text-text3 shrink-0" />
      <select
        value={activeFarmId ?? ""}
        data-testid="farm-switcher"
        onChange={(e) => onSwitch(e.target.value)}
        className="bg-surface border border-border text-text text-xs font-semibold max-w-[180px] px-2 py-1.5 rounded-md outline-none focus:border-primary cursor-pointer"
      >
        {farms.map((f) => (
          <option key={f.id} value={f.id}>{f.name}</option>
        ))}
      </select>
    </div>
  );
}
