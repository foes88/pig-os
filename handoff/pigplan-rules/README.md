# PigPlan AI Rule Engine — PigOS 핸드오프 자산

레거시 PigPlan(KR)의 AI 룰 엔진을 PigOS로 이식하기 위한 참고 자산.
**원칙: 레거시는 "무엇이 필요한가"의 지식 참고용. 구현은 PigOS 네이티브로.**

## 파일

| 파일 | 용도 |
|---|---|
| `pigplan_ai_rules.json` | KR 룰셋 원본 136개 (기계 파싱용). 출처: 운영 DB `TS_INS_AI_RULES` (SSOT). 각 룰 = `{ruleGroup, ruleCode, ruleNm, ruleType(MD/JSON/PROMPT), ruleContent, useYn, description, updDt}` |
| `pigplan_ai_rules_reference.md` | 위 룰셋을 17그룹별로 정리한 사람 읽기용 본문 전체 |
| `pigplan_pigos_rule_coverage.md` | KR 룰 ↔ PigOS `engine/rules/*.py` 커버리지 매핑 (✅있음 45 / ⚠️seed 44 / 🆕신규 47) — **키워드 자동 1차 초안, 본문 보고 확정 필요** |

## KR 룰 엔진 작동 방식 (참고)
- `TS_INS_AI_RULES` = Single Source of Truth. 룰 본문은 `ruleContent`(MD 또는 JSON).
- inspig-ai `rules-loader.ts`가 `USE_YN='Y'`만 15분 캐시로 로딩 → 11그룹으로 묶어 AI 시스템프롬프트에 주입.
- JSON 룰은 임계값으로 코드에서 직접 사용(`getJsonRule(group, code)`).

## PigOS 적용 방침
1. **✅ 있음** (45) — PigOS `engine/rules/*.py`에 대응 룰 존재(psy/npd/farrowing/wsi/rts/pwmr/abortion/disease/inventory). 본문 대조 후 보강만.
2. **⚠️ seed** (44) — 임계값/파라미터(JSON). PigOS는 코드수정 없이 `default_metric_values`(scope: 국가/지역/농가) + `ctx.extra["rule_configs"]`(운영자 룰별 임계값)로 주입. **국가별 차이는 여기서 흡수.**
3. **🆕 신규** (47) — PigOS에 없는 로직/지식. 그 국가가 중시하는 것만 선별해 신규 `Rule`로 작성(scope/ComplianceProfile 게이팅). KR 특화(PCODE·TC_CODE 참조·질병 크롤링 등)는 복제 금지, 재해석.

## 현지화 전략
규칙 로직(번식 생물학)은 전세계 공통 → 재작성 금지. 국가 차이는 scope 데이터(seed)로, 신규는 게이팅된 별도 Rule로. `if country==...` 하드코딩 금지.

## 갱신
KR 룰은 운영 DB에서 계속 갱신됨. 자동 동기화 안 함 — 마일스톤마다 `TS_INS_AI_RULES` 재export(RULE_CONTENT 포함, UTF-8) → diff 리뷰 → 수동 반영.
