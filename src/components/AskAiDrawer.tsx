"use client";

import { useState, useRef, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { chatApi } from "@/lib/api/endpoints/chat";
import { useAuthStore } from "@/store/auth.store";
import type { ChatResponse } from "@/types/api.types";

interface AskAiDrawerProps {
  open: boolean;
  onClose: () => void;
  context?: string | null;
  lang?: "en" | "ko";
}

const SUGGESTED = {
  ko: ["PSY가 왜 낮아요?", "비생산일수 현황", "분만율 미달 이유", "오늘 이슈 요약"],
  en: ["Why is PSY low?", "NPD status", "Farrowing rate miss", "Today's issues"],
};

type Msg = { role: "user"; text: string } | { role: "ai"; response: ChatResponse };

export function AskAiDrawer({ open, onClose, context, lang = "ko" }: AskAiDrawerProps) {
  const farmId = useAuthStore((s) => s.activeFarmId);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, open]);

  const mutation = useMutation({
    mutationFn: (q: string) => chatApi.query(farmId!, { question: q, locale: lang }),
    onSuccess: (data) => setMessages((p) => [...p, { role: "ai", response: data }]),
    onError: () => setMessages((p) => [...p, {
      role: "ai",
      response: { intent: "error", severity: "CRITICAL", answer: lang === "ko" ? "응답 오류가 발생했습니다." : "An error occurred.", findings: [], farm_id: farmId ?? "", as_of: "", renderer: "template" },
    }]),
  });

  const send = (text: string) => {
    if (!text.trim() || !farmId || mutation.isPending) return;
    setMessages((p) => [...p, { role: "user", text }]);
    setInput("");
    mutation.mutate(text);
  };

  const header = lang === "ko" ? "PigOS AI" : "PigOS AI";
  const placeholder = lang === "ko" ? "농장 KPI나 문제 상황을 질문하세요…" : "Ask about your farm KPIs…";

  return (
    <>
      {/* Backdrop */}
      {open && (
        <div className="fixed inset-0 bg-black/20 z-[90] md:bg-transparent" onClick={onClose} />
      )}

      {/* Drawer */}
      <div
        className={`fixed top-0 right-0 h-full w-full md:w-[380px] bg-surface border-l border-border z-[100] flex flex-col shadow-2xl transition-transform duration-300 ${
          open ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-border flex-shrink-0">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center text-white text-sm"
              style={{ background: "linear-gradient(135deg,#2563EB,#7C3AED)" }}>
              ✦
            </div>
            <div>
              <div className="text-sm font-bold text-text">{header}</div>
              <div className="text-[10px] text-muted">Rule Engine 기반 분석</div>
            </div>
          </div>
          <button onClick={onClose} className="w-7 h-7 rounded-full bg-bg2 flex items-center justify-center text-muted hover:text-text transition text-sm">
            ✕
          </button>
        </div>

        {/* Context chip */}
        {context && (
          <div className="px-4 pt-3">
            <span className="inline-flex items-center gap-1 text-[11px] bg-primary-soft text-primary px-2.5 py-1 rounded-full font-medium">
              📌 {context}
            </span>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
          {messages.length === 0 && (
            <div className="space-y-2 mt-2">
              <p className="text-xs text-muted font-medium">{lang === "ko" ? "추천 질문" : "Suggested"}</p>
              {SUGGESTED[lang].map((q) => (
                <button
                  key={q}
                  onClick={() => send(q)}
                  className="w-full text-left px-3 py-2 rounded-lg border border-border bg-bg text-xs text-text2 hover:bg-bg2 hover:border-primary transition"
                >
                  {q}
                </button>
              ))}
            </div>
          )}

          {messages.map((msg, i) =>
            msg.role === "user" ? (
              <div key={i} className="flex justify-end">
                <div className="bg-navy text-white rounded-2xl rounded-tr-sm px-3 py-2 text-xs max-w-[80%]">
                  {msg.text}
                </div>
              </div>
            ) : (
              <div key={i} className="flex justify-start">
                <div className="bg-bg2 border border-border rounded-2xl rounded-tl-sm px-3 py-2.5 text-xs max-w-[90%]">
                  <p className="text-text leading-relaxed">{msg.response.answer}</p>
                  {msg.response.findings.slice(0, 2).map((f, j) => (
                    <div key={j} className="mt-2 pt-2 border-t border-border">
                      <span className="font-mono font-bold text-primary">{f.kpi}</span>
                      {f.current_value != null && (
                        <span className="text-muted ml-1">{f.current_value.toFixed(1)} / {f.target_value?.toFixed(1) ?? "-"}</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )
          )}

          {mutation.isPending && (
            <div className="flex gap-1 items-center text-muted text-xs">
              <span className="w-1.5 h-1.5 bg-muted rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="w-1.5 h-1.5 bg-muted rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="w-1.5 h-1.5 bg-muted rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="px-4 py-3 border-t border-border flex-shrink-0">
          <form onSubmit={(e) => { e.preventDefault(); send(input); }} className="flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={placeholder}
              disabled={mutation.isPending}
              className="flex-1 bg-bg border border-border rounded-lg px-3 py-2 text-xs outline-none focus:border-primary transition"
            />
            <button
              type="submit"
              disabled={!input.trim() || mutation.isPending || !farmId}
              className="bg-navy text-white px-3 py-2 rounded-lg text-xs font-semibold disabled:opacity-40 hover:bg-primary transition"
            >
              ↑
            </button>
          </form>
        </div>
      </div>
    </>
  );
}
