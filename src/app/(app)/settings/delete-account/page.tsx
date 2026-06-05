"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

export default function DeleteAccountPage() {
  const [confirm, setConfirm] = useState("");
  const router = useRouter();
  const canDelete = confirm === "삭제합니다";

  return (
    <div className="max-w-xl mx-auto px-7 py-6">
      <h1 className="text-xl font-extrabold tracking-tight mb-5">계정 삭제</h1>
      <div className="bg-surface border border-border rounded-2xl p-6">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-11 h-11 rounded-xl bg-red-50 flex items-center justify-center shrink-0">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#DC2626" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
            </svg>
          </div>
          <div>
            <div className="text-base font-bold text-text">정말 계정을 삭제하시겠어요?</div>
            <div className="text-xs text-text3 mt-0.5">이 작업은 되돌릴 수 없습니다</div>
          </div>
        </div>
        <div className="bg-red-50 border border-red-100 rounded-xl p-4 mb-5">
          <div className="text-xs font-bold text-danger mb-2">삭제 시 사라지는 데이터</div>
          {["모돈 기록 전체","농장 운영 데이터","AI 분석 및 보고서","구독 및 결제 정보"].map((x,i) => (
            <div key={i} className="text-xs text-text2 flex items-center gap-2 py-1">
              <span className="text-danger font-bold">✕</span>{x}
            </div>
          ))}
        </div>
        <p className="text-xs text-text3 leading-relaxed mb-5">
          삭제 전 데이터를 내보내시려면{" "}
          <span className="text-primary font-semibold cursor-pointer">전체 데이터 내보내기(Excel)</span>를 먼저 진행하세요.
          삭제 후 30일간 복구 문의가 가능하나, 이후 영구 삭제됩니다.
        </p>
        <div className="mb-5">
          <label className="block text-xs font-semibold text-text2 mb-2">
            확인을 위해 <span className="font-mono font-bold text-text">삭제합니다</span>를 입력하세요
          </label>
          <input
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            placeholder="삭제합니다"
            className="input w-full"
          />
        </div>
        <div className="flex gap-2">
          <button onClick={() => router.back()}
            className="flex-1 bg-surface border border-border text-text2 py-3 rounded-xl text-sm font-semibold hover:bg-border transition">
            취소
          </button>
          <button
            disabled={!canDelete}
            className="flex-1 bg-danger text-white py-3 rounded-xl text-sm font-bold disabled:opacity-40 hover:opacity-90 transition">
            계정 영구 삭제
          </button>
        </div>
      </div>
    </div>
  );
}
