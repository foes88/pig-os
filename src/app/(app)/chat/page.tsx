"use client";

import { useState, useRef, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { chatApi } from "@/lib/api/endpoints/chat";
import { useAuthStore } from "@/store/auth.store";
import type { ChatResponse, FindingOut } from "@/types/api.types";

const SEVERITY_COLOR: Record<string, string> = {
  OK:       "border-green-200 bg-green-50",
  INFO:     "border-blue-200 bg-blue-50",
  WARNING:  "border-amber-200 bg-amber-50",
  CRITICAL: "border-red-200 bg-red-50",
};

const SEVERITY_TEXT: Record<string, string> = {
  OK:       "text-green-700",
  INFO:     "text-blue-700",
  WARNING:  "text-amber-700",
  CRITICAL: "text-red-700",
};

const SUGGESTED = [
  "PSY가 왜 낮아요?",
  "비생산일수 현황 알려줘",
  "분만율이 목표 미달인 이유는?",
  "지금 가장 시급한 문제가 뭐야?",
];

type Message =
  | { role: "user"; text: string }
  | { role: "assistant"; response: ChatResponse };

export default function ChatPage() {
  const farmId = useAuthStore((s) => s.activeFarmId);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const mutation = useMutation({
    mutationFn: (question: string) =>
      chatApi.query(farmId!, { question, locale: "ko" }),
    onSuccess: (data) => {
      setMessages((prev) => [...prev, { role: "assistant", response: data }]);
    },
    onError: () => {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          response: {
            intent: "error",
            severity: "CRITICAL",
            answer: "응답을 가져오지 못했습니다. API 서버 연결을 확인해주세요.",
            findings: [],
            farm_id: farmId ?? "",
            as_of: new Date().toISOString().slice(0, 10),
            renderer: "template",
          },
        },
      ]);
    },
  });

  const send = (text: string) => {
    if (!text.trim() || !farmId || mutation.isPending) return;
    setMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");
    mutation.mutate(text);
  };

  if (!farmId) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-text3">농장을 선택해주세요.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)] pb-16 md:pb-0">
        {/* Header */}
        <div className="px-7 py-4 border-b border-border bg-surface flex items-center gap-3">
          <div>
            <h1 className="text-base font-extrabold tracking-tight">Q&A</h1>
            <p className="text-[11px] text-text3">Rule Engine 기반 농장 데이터 분석</p>
          </div>
          <span className="ml-auto text-[9px] font-bold bg-gradient-to-r from-purple-500 to-blue-500 text-white px-2 py-0.5 rounded">
            BASE
          </span>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-7 py-5 space-y-5">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full gap-6 text-center">
              <div>
                <p className="text-lg font-bold text-text1 mb-1">농장 데이터에 대해 질문하세요</p>
                <p className="text-xs text-text3">Rule Engine이 PSY·NPD·분만율 등을 분석해드립니다</p>
              </div>
              <div className="flex flex-wrap gap-2 justify-center">
                {SUGGESTED.map((q) => (
                  <button
                    key={q}
                    onClick={() => send(q)}
                    className="px-4 py-2 rounded-full border border-border bg-surface text-xs text-text2 hover:bg-border hover:text-text1 transition"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) =>
            msg.role === "user" ? (
              <div key={i} className="flex justify-end">
                <div className="bg-primary text-white rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm max-w-[70%]">
                  {msg.text}
                </div>
              </div>
            ) : (
              <AssistantMessage key={i} response={msg.response} />
            )
          )}

          {mutation.isPending && (
            <div className="flex items-center gap-2 text-text3 text-xs">
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 bg-text3 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-1.5 h-1.5 bg-text3 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-1.5 h-1.5 bg-text3 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
              Rule Engine 분석 중...
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="px-7 py-4 border-t border-border bg-surface">
          {messages.length > 0 && (
            <div className="flex gap-2 mb-3 flex-wrap">
              {SUGGESTED.map((q) => (
                <button
                  key={q}
                  onClick={() => send(q)}
                  className="px-3 py-1 rounded-full border border-border text-[11px] text-text3 hover:bg-border transition"
                >
                  {q}
                </button>
              ))}
            </div>
          )}
          <form
            onSubmit={(e) => { e.preventDefault(); send(input); }}
            className="flex gap-2"
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="농장 KPI나 문제 상황을 질문하세요..."
              className="flex-1 px-4 py-2.5 rounded-xl border border-border bg-background text-sm outline-none focus:border-primary transition"
              disabled={mutation.isPending}
            />
            <button
              type="submit"
              disabled={!input.trim() || mutation.isPending}
              className="bg-primary text-white px-5 py-2.5 rounded-xl text-sm font-semibold disabled:opacity-50 hover:bg-primary/90 transition"
            >
              전송
            </button>
          </form>
        </div>
    </div>
  );
}

function AssistantMessage({ response }: { response: ChatResponse }) {
  const borderCls = SEVERITY_COLOR[response.severity] ?? SEVERITY_COLOR.INFO;
  const textCls = SEVERITY_TEXT[response.severity] ?? SEVERITY_TEXT.INFO;

  return (
    <div className="flex justify-start max-w-[85%]">
      <div className={`border rounded-2xl rounded-tl-sm px-5 py-4 w-full ${borderCls}`}>
        {/* Answer */}
        <p className={`text-sm font-medium leading-relaxed ${textCls}`}>{response.answer}</p>

        {/* Findings */}
        {response.findings.length > 0 && (
          <div className="mt-3 space-y-2">
            {response.findings.map((f, i) => (
              <FindingCard key={i} finding={f} />
            ))}
          </div>
        )}

        {/* Meta */}
        <div className="flex items-center gap-2 mt-3 pt-3 border-t border-current/10">
          <span className={`text-[10px] opacity-60 ${textCls}`}>
            기준일 {response.as_of} · {response.renderer === "llm" ? "AI 분석" : "Rule Engine"}
          </span>
        </div>
      </div>
    </div>
  );
}

function FindingCard({ finding }: { finding: FindingOut }) {
  const textCls = SEVERITY_TEXT[finding.severity] ?? SEVERITY_TEXT.INFO;
  return (
    <div className="bg-white/60 rounded-xl px-4 py-3 text-xs">
      <div className={`font-bold mb-1 ${textCls}`}>
        {finding.kpi}
        {finding.current_value != null && (
          <span className="font-normal ml-2">
            현재 {finding.current_value.toFixed(1)} / 목표 {finding.target_value?.toFixed(1) ?? "-"}
          </span>
        )}
      </div>
      {finding.causes.length > 0 && (
        <div className="text-text2 mb-1">
          원인: {finding.causes.join(" · ")}
        </div>
      )}
      {finding.recommended_actions.length > 0 && (
        <div className="text-text3">
          조치: {finding.recommended_actions.join(" · ")}
        </div>
      )}
    </div>
  );
}
