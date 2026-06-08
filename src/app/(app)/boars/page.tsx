"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "@/store/auth.store";
import { boarsApi, type Boar } from "@/lib/api/endpoints/boars";

const STATUS_LABEL: Record<string, string> = {
  ACTIVE: "활성",
  CULLED: "도태",
  DEAD: "폐사",
  TRANSFERRED: "전출",
};

const STATUS_CLASS: Record<string, string> = {
  ACTIVE:      "bg-green-50 text-green-700 border-green-100",
  CULLED:      "bg-red-50 text-red-500 border-red-100",
  DEAD:        "bg-gray-100 text-gray-400 border-gray-200",
  TRANSFERRED: "bg-amber-50 text-amber-600 border-amber-100",
};

export default function BoarsPage() {
  const activeFarmId = useAuthStore((s) => s.activeFarmId);
  const farmId = activeFarmId ?? "";
  const [statusFilter, setStatusFilter] = useState<string>("");

  const { data: boars = [], isLoading, error } = useQuery({
    queryKey: ["boars", farmId, statusFilter],
    queryFn: () => boarsApi.list(farmId, statusFilter || undefined),
    enabled: !!farmId,
  });

  const activeCount = boars.filter((b) => b.status === "ACTIVE").length;

  return (
    <main className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-text">웅돈 관리</h1>
          <p className="text-sm text-text3 mt-0.5">활성 웅돈 {activeCount}두</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-sm border border-border rounded-lg px-3 py-1.5 bg-surface text-text focus:outline-none focus:ring-2 focus:ring-primary/30"
          >
            <option value="">전체 상태</option>
            <option value="ACTIVE">활성</option>
            <option value="CULLED">도태</option>
            <option value="DEAD">폐사</option>
            <option value="TRANSFERRED">전출</option>
          </select>
        </div>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="text-sm text-text3 py-12 text-center">로딩 중...</div>
      ) : error ? (
        <div className="text-sm text-danger py-12 text-center">데이터를 불러오지 못했습니다</div>
      ) : boars.length === 0 ? (
        <div className="text-sm text-text3 py-12 text-center">
          {statusFilter ? "해당 상태의 웅돈이 없습니다" : "등록된 웅돈이 없습니다"}
        </div>
      ) : (
        <div className="bg-surface border border-border rounded-xl overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-bg2">
                <th className="text-left px-4 py-3 text-text3 font-medium">이표번호</th>
                <th className="text-left px-4 py-3 text-text3 font-medium">품종</th>
                <th className="text-left px-4 py-3 text-text3 font-medium">도입일</th>
                <th className="text-left px-4 py-3 text-text3 font-medium">정액 품질</th>
                <th className="text-left px-4 py-3 text-text3 font-medium">상태</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {boars.map((boar: Boar) => (
                <tr key={boar.id} className="hover:bg-bg2/50 transition-colors">
                  <td className="px-4 py-3 font-mono font-semibold text-text">{boar.ear_tag}</td>
                  <td className="px-4 py-3 text-text1">{boar.breed ?? "—"}</td>
                  <td className="px-4 py-3 text-text2">{boar.entry_date.slice(0, 10)}</td>
                  <td className="px-4 py-3 text-text2">{boar.semen_quality ?? "—"}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${STATUS_CLASS[boar.status] ?? "bg-gray-50 text-gray-500"}`}>
                      {STATUS_LABEL[boar.status] ?? boar.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </main>
  );
}
