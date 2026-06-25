# 야간 무인 실행 로그 — A-하이브리드 T1-3~T1-6

> 2026-06-25 시작. dev 전용. push/배포 없음. STOP-on-FAIL.

## §0 선행 게이트 — ✅ PASS
- git branch=main (프로젝트 관례, push는 사람 수동 — "dev"는 환경 의미로 해석)
- working tree: 코드 mutation 0 (benchmark_thresholds.py = CRLF만, 내용변경 0). UAT 스크린샷·untracked handoff는 세션 전 무관 노이즈(범위 밖).
- alembic head = f2b4d6e8a0c1 ✓
- USE_GOVERNANCE_BENCHMARKS = False ✓
- baseline: **587 passed** ✓
- (Docker postgres 다운 1회 → 재기동 복구 후 통과)

---
## 게이트 1 — T1-3 Threshold Resolver — ✅ PASS
- threshold_resolver.py(gov_resolve_thresholds) + _common.resolve/reproduction flag 분기
- flag ON: rule_config→operational_defaults→code (옛 default_metric_values 제외). flag OFF: 기존 경로 유지.
- 테스트: T1-3 35 + 전체 **622 passed** (flag OFF 587 전부 유지 = 동작 변화 0)
- 커밋: 1675ebe
- 명령: uv run pytest tests/unit/test_threshold_resolver_t13.py / uv run pytest tests/

## 게이트 2 — T1-4 Benchmark Context Resolver — ✅ PASS
- resolve_benchmark_context(): verified/normalized 맥락첨부, provisional·missing 금지, value_scale mismatch 맥락만 강등, global_fallback trace
- 테스트: T1-4 8 + 전체 **630 passed**
- 커밋: 83427d6

## 게이트 3 — T1-5 엔진 배선 + trace — ✅ PASS
- build_rule_context 2곳 operational_defaults 주입(flag ON) + enrich_findings_with_governance(§7 trace, RULE_KPI_TO_GOVERNANCE 매핑)
- chat/dashboard flag-gated 호출. 테스트 T1-5 5 + 전체 **635 passed**. 커밋 241d25a

## 게이트 4 — T1-6 before/after diff — ✅ PASS (검증 관문)
- 고정 fixture(KR/US/GLOBAL) flag OFF vs ON 발화: **KR 18=18 / US 3=3 / GLOBAL 9=9, lost0 gained0**
- operational_defaults=code default → 발화 1:1 보존(§10.2 합격). 절대중단 0건.
- 테스트 T1-6 2 + 전체 **637 passed**. 커밋 b5d4fe5

---
## 종료 리포트
| 게이트 | 결과 | 커밋 | 전체 테스트 |
|---|---|---|---|
| §0 선행 | ✅ | — | 587 baseline |
| 1 T1-3 Threshold Resolver | ✅ PASS | 1675ebe | 622 |
| 2 T1-4 Context Resolver | ✅ PASS | 83427d6 | 630 |
| 3 T1-5 엔진 배선+trace | ✅ PASS | 241d25a | 635 |
| 4 T1-6 diff(관문) | ✅ PASS | b5d4fe5 | **637** |

- **587 → 637 passed** (+50 신규, 0 fail/error)
- T1-6 diff: 전 fixture **발화 유지(이탈 0/신규 0)** — A-하이브리드 발화 보존 입증
- flag `USE_GOVERNANCE_BENCHMARKS` **여전히 OFF**(동작 변화 0). 켜지 않음.
- alembic head 불변 f2b4d6e8a0c1. push/배포 없음.

### 남은 것 / 사람 판단 필요
1. **flag ON 실전환 결정** — flag ON 시 KR/US의 default_metric_values **country override**가 빠지고 operational_defaults(글로벌)+governance 맥락으로 감. country override 영향 평가 후 전환(별도 diff: benchmarks 있는 실농장 fixture). 본 게이트는 override 없는 fixture로 보존만 입증.
2. **base.py 특수형(PSY밴드/NPD/farrowing)**: flag ON에서도 ctx.benchmarks(default_metric_values) 읽음 — §14.6 완전 준수하려면 base도 operational_defaults화 필요(㉮로 코드유지 선택해 미적용). flag ON 전 결정.
3. 운영 배포(T3) / EU·GB(D-3) / BR·VN(자료) — 대기.

