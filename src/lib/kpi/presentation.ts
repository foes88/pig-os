/**
 * Presentation Policy 적용 — 서버가 확정한 카드 목록을 렌더 메타와 결합한다.
 *
 * ★ 프론트는 재계산하지 않는다.
 *   - items 는 서버가 정렬을 끝낸 상태 → 순서 그대로 사용(재정렬 금지)
 *   - HIDDEN 은 서버가 이미 제외 → 프론트 필터 불필요
 *   - headline 은 headline_kpi 필드 → NORTH_STAR 를 프론트가 탐색하지 않음
 *   - severity 는 kpi_status 소관 → 여기서 생성·변환하지 않음
 *
 * 폴백(A3): presentation 이 없거나(미로드·404·timeout) items 가 비었거나 렌더 가능한
 * 항목이 하나도 없으면 레지스트리 기본 순서로 렌더한다. 국가 추정·국가별 기본 배열 금지.
 */
import { track } from "@/lib/analytics";
import { KPI_CARD_REGISTRY, REGISTRY_BY_CODE, type KpiCardMeta } from "@/lib/kpi/cardRegistry";
import type { KpiPresentation } from "@/types/api.types";

export type ResolvedKpiCard = {
  meta: KpiCardMeta;
  /** 국가 현지 명칭. null 이면 레지스트리 라벨 사용 */
  localLabel: string | null;
  isHeadline: boolean;
};

export type ResolvedKpiCards = {
  cards: ResolvedKpiCard[];
  headlineKpi: string | null;
  /** presentation = 서버 정책 적용됨 · fallback = 기본 화면 유지 */
  source: "presentation" | "fallback";
  /** 서버가 보냈지만 레지스트리에 렌더 방법이 없는 코드(관측용) */
  unknownCodes: string[];
};

function fallback(): ResolvedKpiCards {
  return {
    cards: KPI_CARD_REGISTRY.map((meta) => ({ meta, localLabel: null, isHeadline: false })),
    headlineKpi: null,
    source: "fallback",
    unknownCodes: [],
  };
}

/**
 * @param presentation GET /kpi/presentation 응답. undefined = 미로드/실패
 * @param registryCodes 이 화면이 렌더할 수 있는 KPI 코드 제한(미지정 = 전체 레지스트리)
 */
export function resolveKpiCards(
  presentation: KpiPresentation | undefined | null,
  registryCodes?: readonly string[],
): ResolvedKpiCards {
  const allowed = registryCodes ? new Set(registryCodes) : null;
  const base = allowed
    ? KPI_CARD_REGISTRY.filter((m) => allowed.has(m.kpi_code))
    : KPI_CARD_REGISTRY;

  if (!presentation || !Array.isArray(presentation.items) || presentation.items.length === 0) {
    const fb = fallback();
    return { ...fb, cards: base.map((meta) => ({ meta, localLabel: null, isHeadline: false })) };
  }

  const cards: ResolvedKpiCard[] = [];
  const unknownCodes: string[] = [];
  for (const item of presentation.items) {
    const meta = REGISTRY_BY_CODE.get(item.kpi_code);
    if (!meta) {
      // Presentation 에는 있는데 Registry 에 없음 — 렌더 방법을 모르므로 건너뛴다(크래시 금지).
      unknownCodes.push(item.kpi_code);
      continue;
    }
    if (allowed && !allowed.has(item.kpi_code)) continue; // 이 화면이 다루지 않는 KPI
    cards.push({
      meta,
      localLabel: item.local_label ?? null,
      isHeadline: item.kpi_code === presentation.headline_kpi,
    });
  }

  // 렌더 가능한 항목이 하나도 없으면 화면이 비므로 기본 화면으로 안전 복귀.
  if (cards.length === 0) {
    const fb = fallback();
    return {
      ...fb,
      cards: base.map((meta) => ({ meta, localLabel: null, isHeadline: false })),
      unknownCodes,
    };
  }

  return {
    cards,
    headlineKpi: presentation.headline_kpi ?? null,
    source: "presentation",
    unknownCodes,
  };
}

/** 레지스트리·정책 불일치 관측. 양방향 모두 앞으로 반드시 생긴다. */
export function reportPresentationGaps(resolved: ResolvedKpiCards): void {
  for (const code of resolved.unknownCodes) {
    track("kpi_presentation_unknown_code", { kpi_code: code, source: resolved.source });
  }
  if (resolved.source === "fallback") {
    track("kpi_presentation_fallback", { reason: resolved.unknownCodes.length ? "no_renderable_item" : "absent_or_empty" });
  }
}
