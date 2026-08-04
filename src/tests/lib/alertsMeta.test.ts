import { describe, it, expect } from "vitest";
import {
  ALERT_META,
  ALL_OVERDUE_TYPES,
  SEVERITY_BAND,
  SEVERITY_PILL,
  type Severity,
} from "@/lib/alerts/meta";

// 알림 메타 = 설명가능 AI 근거(임계·심각도·조치). 백엔드 alert_service와 임계 정합.

const SEVERITIES: Severity[] = ["critical", "warning", "info"];
const ACTIONS = ["mating", "farrowing", "weaning"];

describe("ALERT_META 구조 불변식", () => {
  it("6유형 모두 존재", () => {
    expect(ALL_OVERDUE_TYPES).toHaveLength(6);
  });
  it("각 엔트리: 유효 severity·action·양수 threshold·비어있지 않은 조치키", () => {
    for (const t of ALL_OVERDUE_TYPES) {
      const m = ALERT_META[t];
      expect(SEVERITIES).toContain(m.severity);
      expect(ACTIONS).toContain(m.action);
      expect(m.threshold).toBeGreaterThan(0);
      expect(m.labelKey.length).toBeGreaterThan(0);
      expect(m.ruleKey.length).toBeGreaterThan(0);
      expect(m.actionKeys.length).toBeGreaterThan(0);
    }
  });
});

describe("임계값 고정 (백엔드 정합)", () => {
  it("분만초과=114·이유초과=21·교배초과(open/accident)=7·gilt=240", () => {
    expect(ALERT_META.pregnant_overdue_farrowing.threshold).toBe(114);
    expect(ALERT_META.lactating_overdue_weaning.threshold).toBe(21);
    expect(ALERT_META.open_overdue_mating.threshold).toBe(7);
    expect(ALERT_META.accident_overdue_mating.threshold).toBe(7);
    expect(ALERT_META.gilt_overdue_mating.threshold).toBe(240);
    expect(ALERT_META.gilt_no_estrus.threshold).toBe(240);
  });
  it("심각도 분류: 분만·공태초과=critical, gilt무발정=info", () => {
    expect(ALERT_META.pregnant_overdue_farrowing.severity).toBe("critical");
    expect(ALERT_META.open_overdue_mating.severity).toBe("critical");
    expect(ALERT_META.gilt_no_estrus.severity).toBe("info");
  });
});

describe("SEVERITY 스타일 맵", () => {
  it("3개 심각도 모두 band·pill 클래스 보유", () => {
    for (const s of SEVERITIES) {
      expect(SEVERITY_BAND[s]).toBeTruthy();
      expect(SEVERITY_PILL[s]).toBeTruthy();
    }
  });
});
