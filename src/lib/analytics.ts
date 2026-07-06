// 경량 제품 계측 (PostHog) — 별도 의존성/번들 없이 capture API 직접 호출.
// NEXT_PUBLIC_POSTHOG_KEY 미설정 시 전부 no-op → 로컬/키없음 환경 안전.
// 퍼널: signup → sow_added → event_added → dashboard_viewed → (재방문) app_opened.

const KEY = process.env.NEXT_PUBLIC_POSTHOG_KEY;
const HOST = (process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://us.i.posthog.com").replace(/\/+$/, "");
const DID_KEY = "ph_did";

function enabled(): boolean {
  return !!KEY && typeof window !== "undefined";
}

/** 로그인 전엔 익명 id, 로그인/가입 시 userId로 승격(identifyUser). */
function distinctId(): string {
  if (typeof window === "undefined") return "server";
  let id = localStorage.getItem(DID_KEY);
  if (!id) {
    id =
      "anon_" +
      (typeof crypto !== "undefined" && crypto.randomUUID
        ? crypto.randomUUID()
        : Math.random().toString(36).slice(2) + Date.now().toString(36));
    localStorage.setItem(DID_KEY, id);
  }
  return id;
}

function send(payload: Record<string, unknown>): void {
  if (!enabled()) return;
  try {
    const body = JSON.stringify(payload);
    const url = `${HOST}/capture/`;
    if (typeof navigator !== "undefined" && navigator.sendBeacon) {
      navigator.sendBeacon(url, new Blob([body], { type: "application/json" }));
    } else {
      void fetch(url, {
        method: "POST",
        body,
        headers: { "Content-Type": "application/json" },
        keepalive: true,
      }).catch(() => {});
    }
  } catch {
    // 계측 실패는 앱 동작에 영향 주지 않음(조용히 무시)
  }
}

/** 이벤트 기록. props는 자유 형식(개인정보 금지 — id/집계 값만). */
export function track(event: string, properties: Record<string, unknown> = {}): void {
  if (!enabled()) return;
  send({
    api_key: KEY,
    event,
    distinct_id: distinctId(),
    properties: { ...properties, $current_url: window.location.href, source: "pigos-web" },
    timestamp: new Date().toISOString(),
  });
}

/** 로그인/가입 시 호출 — 익명 세션을 userId에 연결(퍼널·리텐션용). 개인정보(이메일 등) 넣지 말 것. */
export function identifyUser(userId: string, properties: Record<string, unknown> = {}): void {
  if (!enabled() || !userId) return;
  const prev = typeof window !== "undefined" ? localStorage.getItem(DID_KEY) : null;
  if (typeof window !== "undefined") localStorage.setItem(DID_KEY, userId);
  send({
    api_key: KEY,
    event: "$identify",
    distinct_id: userId,
    properties: {
      $set: properties,
      ...(prev && prev !== userId ? { $anon_distinct_id: prev } : {}),
    },
    timestamp: new Date().toISOString(),
  });
}

/** 로그아웃 시 호출 — 다음 방문자와 세션 섞이지 않게 익명 id 리셋. */
export function resetAnalytics(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(DID_KEY);
}
