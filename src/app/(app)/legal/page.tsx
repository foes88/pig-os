"use client";
import { useState } from "react";

export default function LegalPage() {
  const [tab, setTab] = useState<"terms" | "privacy">("terms");
  return (
    <div className="max-w-3xl mx-auto px-7 py-6">
      <h1 className="text-xl font-extrabold tracking-tight mb-5">약관 및 정책</h1>
      <div className="flex gap-2 mb-5">
        {([["terms","이용약관"],["privacy","개인정보처리방침"]] as const).map(([k,l]) => (
          <button key={k} onClick={() => setTab(k)}
            className={`px-5 py-2 rounded-xl text-sm font-semibold border transition ${
              tab === k ? "bg-navy text-white border-navy" : "bg-surface border-border text-text2 hover:bg-border"
            }`}>{l}</button>
        ))}
      </div>
      <div className="bg-surface border border-border rounded-2xl p-6">
        <p className="text-[11px] text-text3 font-mono mb-5">최종 개정 2026-05-01 · v2.3</p>
        {tab === "terms" ? (
          <div className="space-y-5">
            {[
              ["제1조 (목적)","본 약관은 WiseLake(이하 '회사')가 제공하는 PigOS 서비스의 이용 조건 및 절차, 회사와 회원 간 권리·의무를 규정함을 목적으로 합니다."],
              ["제2조 (정의)",'"서비스"란 회사가 제공하는 양돈 농장 관리 및 AI 분석 플랫폼을 의미합니다. "회원"이란 본 약관에 동의하고 이용계약을 체결한 자를 말합니다.'],
              ["제3조 (데이터 소유권)","회원이 입력한 농장 데이터의 소유권은 회원에게 있으며, 회사는 서비스 제공 및 익명화된 벤치마크 목적으로만 이를 활용합니다."],
              ["제4조 (서비스 변경·중단)","회사는 운영상 필요에 따라 서비스를 변경하거나 중단할 수 있으며, 이 경우 사전에 공지합니다."],
            ].map(([h,b],i) => (
              <div key={i}>
                <div className="text-sm font-bold text-text mb-1.5">{h}</div>
                <p className="text-sm text-text2 leading-relaxed">{b}</p>
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-5">
            {[
              ["1. 수집하는 개인정보","회원가입 시 이름, 이메일, 농장 정보를 수집합니다. 서비스 이용 과정에서 농장 운영 데이터가 저장됩니다."],
              ["2. 이용 목적","서비스 제공, AI 분석, 익명화된 벤치마크 산출, 고객 지원에 활용됩니다."],
              ["3. 보유 및 파기","회원 탈퇴 시 즉시 파기하며, 법령상 보존 의무가 있는 경우 해당 기간 동안 보관 후 파기합니다."],
              ["4. k-익명성 보호","벤치마크 데이터는 k≥10으로 익명화되어 개별 농장이 식별되지 않습니다."],
            ].map(([h,b],i) => (
              <div key={i}>
                <div className="text-sm font-bold text-text mb-1.5">{h}</div>
                <p className="text-sm text-text2 leading-relaxed">{b}</p>
              </div>
            ))}
          </div>
        )}
      </div>
      <p className="text-xs text-text3 text-center mt-4">
        전문 다운로드 (PDF) · 문의 <span className="text-primary">legal@pigos.io</span>
      </p>
    </div>
  );
}
