/**
 * KPI 카드 메타데이터 레지스트리 — "이 KPI 를 어떻게 그리는가"만 담는다.
 *
 * 층 분리:
 *   registry(여기)          렌더 방법 — 값 접근자·단위·설명·spark 소스·invert
 *   /kpi/presentation       무엇을·어떤 순서로·무슨 이름으로  (국가별, 서버 확정)
 *   /kpi/dashboard          숫자 그 자체
 *   kpi_status(ADR-KPI-08)  severity 판정 결과
 *
 * ★ 여기에 국가 분기·임계값·판정·숫자 재계산을 넣지 말 것.
 *   국가 확장은 코드가 아니라 country_kpi_presentation 데이터로 한다.
 */
import type { KpiDashboard, KpiTrend } from "@/types/api.types";

export type KpiCardMeta = {
  /** country_kpi_policy.kpi_code 와 동일한 정본 코드 */
  kpi_code: string;
  /** next-intl 메시지 키 — 네임스페이스 "kpiCards"(대시보드/KPI 페이지 공용).
   *  presentation.local_label 이 있으면 그쪽이 우선한다. */
  labelKey: string;
  /** 라벨을 번역하지 않고 코드 그대로 쓰는 경우(PSY 등) */
  literalLabel?: string;
  descKey?: string;
  unitKey?: string;
  /** data.benchmarks 의 키. 없으면 벤치마크 비교 미표시 */
  benchKey?: string;
  /** 낮을수록 좋은 지표(NPD 등) */
  invert?: boolean;
  /** 값 접근자 — 원값 그대로. 스케일 변환·대체 상수 금지. null = 값 없음 */
  value: (d: KpiDashboard) => number | null;
  /** 값 표기 소수 자릿수 */
  digits: number;
  /** spark/trend 소스 — 없으면 미표시 */
  series?: (t: KpiTrend[]) => (number | null)[];
};

/**
 * 기본 카드 집합 + 기본 순서.
 * presentation 미로드·실패·빈 items 일 때 이 순서를 그대로 쓴다(A3 폴백).
 * ★ 국가별 기본 배열을 만들지 않는다 — 폴백은 국가 무관 단일 배열이다.
 */
export const KPI_CARD_REGISTRY: readonly KpiCardMeta[] = [
  {
    kpi_code: "PSY",
    labelKey: "labelPSY",
    literalLabel: "PSY",
    descKey: "descPSY",
    benchKey: "PSY",
    value: (d) => d.psy,
    digits: 1,
    series: (t) => t.map((r) => r.psy),
  },
  {
    kpi_code: "NPD",
    labelKey: "labelNPD",
    descKey: "descNPD",
    unitKey: "unitDays",
    benchKey: "NPD",
    invert: true,
    value: (d) => d.npd,
    digits: 1,
    series: (t) => t.map((r) => r.npd),
  },
  {
    kpi_code: "FARROWING_RATE",
    labelKey: "labelFARROWING_RATE",
    descKey: "descFARROWING_RATE",
    unitKey: "unitPercent",
    benchKey: "FARROWING_RATE",
    value: (d) => d.farrowing_rate,
    digits: 1,
    series: (t) => t.map((r) => r.farrowing_rate),
  },
  {
    kpi_code: "SOW_TURNOVER",
    labelKey: "labelSOW_TURNOVER",
    unitKey: "unitLitters",
    value: (d) => d.sow_turnover ?? null,
    digits: 2,
  },
] as const;

export const REGISTRY_BY_CODE: ReadonlyMap<string, KpiCardMeta> = new Map(
  KPI_CARD_REGISTRY.map((m) => [m.kpi_code, m]),
);
