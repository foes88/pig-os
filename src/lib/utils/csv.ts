// 공용 CSV 유틸 — reports 내보내기에서 사용 (기존 동작과 동일하게 유지).
export type CsvCell = string | number | null;

/** 단순 CSV 빌더: null/undefined → 빈칸, 그 외 문자열화. 행은 "\n"으로 결합. */
export function toCsv(headers: string[], rows: CsvCell[][]): string {
  const esc = (v: CsvCell) => (v == null ? "" : `${v}`);
  return [headers.join(","), ...rows.map((r) => r.map(esc).join(","))].join("\n");
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
