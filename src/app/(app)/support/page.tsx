"use client";
import { useState } from "react";

const FAQS = [
  ["데이터를 엑셀로 내보낼 수 있나요?", "네, 설정 > 데이터 내보내기에서 전체 모돈 기록과 보고서를 Excel/PDF로 받을 수 있습니다."],
  ["오프라인에서 입력한 기록은 어떻게 되나요?", "로컬에 저장된 후 인터넷 연결 시 자동으로 동기화됩니다. 동기화 상태는 화면 상단에 표시됩니다."],
  ["AI 손실 추정은 어떻게 계산되나요?", "NPD 지연, 분만율 하락, 폐사 등을 27년 벤치마크와 비교해 금액으로 환산합니다."],
  ["여러 농장을 하나의 계정으로 관리할 수 있나요?", "네, 조직 계정에서 여러 농장을 등록하고 전환하며 사용할 수 있습니다."],
];

export default function SupportPage() {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <div className="max-w-3xl mx-auto px-7 py-6">
      <h1 className="text-xl font-extrabold tracking-tight mb-5">고객지원</h1>

      <div className="grid grid-cols-3 gap-3 mb-7">
        {[["💬","채팅 상담","평일 9–18시"],["📧","이메일","help@pigos.io"],["📞","전화","1588-0000"]].map(([ic,t,s],i) => (
          <div key={i} className="bg-surface border border-border rounded-2xl p-5">
            <div className="text-2xl mb-2">{ic}</div>
            <div className="text-sm font-bold text-text">{t}</div>
            <div className="text-xs text-text3 mt-1">{s}</div>
          </div>
        ))}
      </div>

      <p className="text-xs font-semibold text-text3 tracking-wider font-mono mb-3">자주 묻는 질문</p>
      <div className="space-y-2">
        {FAQS.map(([q, a], i) => (
          <div key={i} className="bg-surface border border-border rounded-2xl overflow-hidden">
            <button
              onClick={() => setOpen(open === i ? null : i)}
              className="w-full flex items-center justify-between px-5 py-4 text-left"
            >
              <span className="text-sm font-semibold text-text">{q}</span>
              <span className="text-text3 text-xs ml-3">{open === i ? "▲" : "▼"}</span>
            </button>
            {open === i && (
              <div className="px-5 pb-4 text-sm text-text2 leading-relaxed border-t border-border pt-3">
                {a}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
