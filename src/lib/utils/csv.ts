// 공용 CSV 유틸 — reports 내보내기에서 사용.
export type CsvCell = string | number | null;

/** 한 셀 이스케이프:
 *  - 수식 인젝션 차단: 문자열이 = + - @ \t \r 로 시작하면 ' 프리픽스 (숫자형은 안전 → 제외).
 *  - 구분자/따옴표/개행 포함 시 따옴표로 감싸고 내부 "는 ""로 이스케이프.
 *  특수문자 없는 일반 값은 원형 그대로(기존 출력과 동일). */
export function escapeCsvCell(v: CsvCell): string {
  if (v == null) return "";
  let s = `${v}`;
  if (typeof v === "string" && /^[=+\-@\t\r]/.test(s)) s = `'${s}`;
  if (/[",\n\r]/.test(s)) s = `"${s.replace(/"/g, '""')}"`;
  return s;
}

/** CSV 빌더: null/undefined → 빈칸, 셀은 인젝션·구분자 안전 이스케이프. 행은 "\n"으로 결합. */
export function toCsv(headers: string[], rows: CsvCell[][]): string {
  return [
    headers.map(escapeCsvCell).join(","),
    ...rows.map((r) => r.map(escapeCsvCell).join(",")),
  ].join("\n");
}

/** BOM(﻿) 포함 CSV를 브라우저에서 다운로드 (한글 Excel 호환). */
export function downloadCsv(filename: string, headers: string[], rows: CsvCell[][]): void {
  const blob = new Blob(["﻿" + toCsv(headers, rows)], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
