// ADR-KPI-08 Phase 2 — dual observation.
// 백엔드 canonical status와 현행 프론트 tier 판정이 얼마나 다른지 "관측만" 한다.
// 사용자 화면 판정은 바꾸지 않는다(전환은 Phase 3).
//
// 왜 하는가: 백엔드가 warning인데 화면이 normal이던 케이스가 곧 놓친 경보이며,
// 이는 재고 분모 결함(D-2)의 간접 증거가 된다.
import { track } from "@/lib/analytics";
import type { KpiStatusDto } from "@/types/api.types";
import type { KpiTier } from "./status";

/** 백엔드 status ↔ 프론트 tier 비교용 정규화. 판정하지 않고 이름만 맞춘다. */
function normalize(v: string): string {
  return v.toLowerCase();
}

export interface StatusMismatch {
  metric: string;
  backend: string;
  backendReason: string | null;
  frontend: KpiTier;
}

/**
 * 불일치 목록을 계산한다(순수 함수 — 로깅은 report* 에서).
 * backend가 insufficient인 경우도 불일치로 본다(프론트가 임의 판정 중이라는 뜻).
 */
export function findStatusMismatches(
  backend: Record<string, KpiStatusDto> | undefined,
  frontend: Record<string, KpiTier>,
): StatusMismatch[] {
  if (!backend) return [];
  const out: StatusMismatch[] = [];
  for (const [metric, fe] of Object.entries(frontend)) {
    const be = backend[metric];
    if (!be) continue;                       // 백엔드가 안 준 지표는 비교 대상 아님
    if (normalize(be.status) !== normalize(fe)) {
      out.push({ metric, backend: be.status, backendReason: be.reason, frontend: fe });
    }
  }
  return out;
}

/**
 * ADR-KPI-08 Phase 3 — 렌더용 tier 결정.
 * 백엔드 canonical status가 있으면 그것을 쓴다(국가별 정책 반영). 프론트는 판정하지 않는다.
 * 백엔드가 status를 주지 않을 때(구버전 API·미배포)만 legacy tier로 폴백한다 — Phase 4에서 제거.
 * 미지의 status 값은 임계 계산으로 되돌아가지 않고 중립(insufficient)으로 렌더한다.
 */
const _CANONICAL: readonly KpiTier[] = ["normal", "warning", "critical", "insufficient"];

export function resolveTier(
  backend: Record<string, KpiStatusDto> | undefined,
  metric: string,
  legacy: KpiTier,
): KpiTier {
  const be = backend?.[metric];
  if (!be) return legacy;                                   // 폴백(Phase 4에서 제거)
  const s = normalize(be.status) as KpiTier;
  return _CANONICAL.includes(s) ? s : "insufficient";       // unknown → 중립, 재판정 금지
}

/** 불일치를 텔레메트리로 보낸다(있을 때만). 화면 동작에는 영향 없음. */
export function reportStatusMismatches(
  backend: Record<string, KpiStatusDto> | undefined,
  frontend: Record<string, KpiTier>,
): StatusMismatch[] {
  const mismatches = findStatusMismatches(backend, frontend);
  for (const m of mismatches) {
    track("kpi_status_mismatch", {
      metric: m.metric,
      backend_status: m.backend,
      backend_reason: m.backendReason,
      frontend_tier: m.frontend,
    });
  }
  return mismatches;
}
