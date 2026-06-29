// FastAPI 에러 응답에서 사람이 읽을 메시지를 추출한다.
// - 도메인 에러(PigOSError): detail = string
// - Pydantic 422: detail = [{ msg, loc }] (배열) — 배열을 무시하면 실제 사유가 사라져
//   사용자에게 항상 generic 폴백만 보이는 버그가 생긴다(C4).
export function apiError(err: unknown, fallback: string): string {
  const detail = (
    err as { response?: { data?: { detail?: string | { msg?: string }[] } } }
  )?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const msgs = detail.map((d) => d?.msg).filter(Boolean);
    if (msgs.length) return msgs.join(", ");
  }
  return fallback;
}
