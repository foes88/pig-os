/**
 * 중앙 아이콘 매핑 — UI 전반의 severity / 번식단계 아이콘을 lucide-react로 일원화.
 * (이모지 대신 프로젝트 표준 아이콘 시스템 lucide 사용. 중복 매핑 제거용 단일 소스.)
 */
import {
  AlertOctagon,
  AlertTriangle,
  Baby,
  CheckCircle2,
  HeartPulse,
  Info,
  Milk,
  Sprout,
  Syringe,
  type LucideIcon,
} from "lucide-react";

// KPI/알림 심각도 → 아이콘 (OK/INFO/WARNING/CRITICAL)
export const SEVERITY_ICON: Record<string, LucideIcon> = {
  OK: CheckCircle2,
  INFO: Info,
  WARNING: AlertTriangle,
  CRITICAL: AlertOctagon,
};

// 번식 파이프라인 단계 → 아이콘 (교배/임신/분만/포유/이유)
export const STAGE_ICON: Record<string, LucideIcon> = {
  MATING: Syringe, // 교배
  PREGNANT: HeartPulse, // 임신
  FARROWING: Baby, // 분만
  LACTATING: Milk, // 포유
  WEANING: Sprout, // 이유
};
