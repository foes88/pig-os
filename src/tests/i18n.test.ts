import { readFileSync } from "fs";
import { resolve } from "path";

import { describe, it, expect } from "vitest";

// 7개 로케일 키 정합성 가드. en을 기준으로 다른 로케일에 누락/잉여 키가 있으면
// 런타임에 생키 노출(예: sowStatus.SOLD) 또는 IntlError가 난다 — 그 클래스를 통째로 차단.
const LOCALES = ["en", "ko", "zh", "es", "vi", "th", "pt"];

function load(locale: string): Record<string, unknown> {
  return JSON.parse(readFileSync(resolve("messages", `${locale}.json`), "utf8"));
}

function flatKeys(obj: unknown, prefix = ""): string[] {
  if (!obj || typeof obj !== "object" || Array.isArray(obj)) return [prefix];
  return Object.entries(obj as Record<string, unknown>).flatMap(([k, v]) =>
    flatKeys(v, prefix ? `${prefix}.${k}` : k),
  );
}

describe("i18n locale parity", () => {
  const base = new Set(flatKeys(load("en")));

  for (const locale of LOCALES.filter((l) => l !== "en")) {
    it(`${locale} 키 집합이 en과 정확히 일치`, () => {
      const keys = new Set(flatKeys(load(locale)));
      const missing = [...base].filter((k) => !keys.has(k));
      const extra = [...keys].filter((k) => !base.has(k));
      expect({ locale, missing, extra }).toEqual({ locale, missing: [], extra: [] });
    });
  }

  it("모든 SowStatus 값이 sowStatus 네임스페이스에 존재(생키 노출 방지)", () => {
    const statuses = ["GILT", "OPEN", "PREGNANT", "LACTATING", "ACCIDENT", "CULLED", "DEAD", "SOLD", "TRANSFER"];
    for (const locale of LOCALES) {
      const msgs = load(locale) as { sowStatus?: Record<string, string> };
      for (const s of statuses) {
        expect(msgs.sowStatus?.[s], `${locale}.sowStatus.${s}`).toBeTruthy();
      }
    }
  });
});
