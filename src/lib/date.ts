// 로컬 캘린더 날짜 유틸. new Date().toISOString()(UTC)은 KST 등 양수 오프셋에서
// 자정~오전 구간에 하루 밀려 폼 기본값이 '어제'로 들어가는 버그가 있어 로컬 기준으로 보정한다.

/** 로컬 기준 오늘 (YYYY-MM-DD). */
export function localToday(): string {
  const d = new Date();
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}

/** 로컬 기준 n일 후/전 (YYYY-MM-DD). */
export function localDateOffset(days: number): string {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}
