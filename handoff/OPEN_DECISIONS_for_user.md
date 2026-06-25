# 사용자 확정/조사 필요 항목 (KPI 거버넌스 D-질문 총정리)

> 기준: handoff/KPI_GOVERNANCE_v3.1.md §5 (D-1~D-12) + D-13 + 세션 발견
> 갱신: 2026-06-25 / 코드가 임의 결정 금지 → 사용자만 풀 수 있는 것들.
> 분류: 🔴 1차자료 조사(알아와야) / 🟡 정책·정의 확정(결정만) / ✅ 해소됨

---

## 🔴 1차자료 조사 필요 (내가 알아와야 — 위조 금지라 코드가 못 채움)

| # | 질문 | 왜 필요 | 막히는 것 |
|---|---|---|---|
| **D-6** | **한돈팜스 공식 PDF** — KR 2025 PSY/MSY가 22.3(4분기)/22.4(전국기사)/22.5(12개월) 중 무엇? period 확정 | KR provisional 10종 → verified 승격 | KR 전체가 provisional에 묶임 |
| **앵커마켓 수치** | **BR(Agriness)·VN(WEPIG)·CN·TH·MX** 1차 KPI 수치 | 국가별 verified 시드 | 해당국 룰 침묵(글로벌 폴백만) |
| (US는 확보됨) | PigCHAMP USA 2025 — 이미 1차검증 완료(사산 9.93%/분만 83.81%) | US 적재 단계서 사용 | — |

> 우선순위: **D-6(한국) ≥ US 적재 ≥ BR/VN(앵커)**. TH/MX는 global_fallback이라 급하지 않음.

---

## 🟡 정책·정의 확정 필요 (조사 아님, 내부 결정만)

| # | 질문 | 잠정 권고 | 언제까지 |
|---|---|---|---|
| **D-1** | NPD에 후보돈 초교배까지 포함? | 내부정의 1개 고정 + `gilt_entry_included` 플래그 | KR verified 전 |
| **D-2** | MSY "출하" 기준시점(판매두수?) | 판매두수 고정 | KR/US verified 전 |
| **D-4** | 미국 PWMFY를 PSY로 재정규화 vs 별도 지표? | **별도(pwmfy), PSY는 missing** (분모=교배모돈, 농장마다 변환계수 달라 불가) | **US 적재 전 ★** |
| **D-5** | 사산율 normalized 계산: 농장단위 가중 vs 집계합산? | 가능하면 농장단위 가중, formula 명시 | **US 적재 전 ★** |
| **D-3** | GB를 country 단위로 볼 때 indoor/outdoor/평균? | MVP 'GB_indoor' 명시 또는 system 예외 | EU/GB 적재 전(후순위) |
| **D-9** | production_system 'all' 고정, GB만 예외? | 컬럼 생성됨, GB만 주석 | EU/GB 적재 전 |

> ★ **D-4·D-5는 다음 단계(US 적재)를 직접 가릅니다.** US verified/normalized를 박기 전에 이 둘만 확정해주시면 됩니다.

---

## ✅ 이번 세션에 해소됨 (참고 — 다시 안 물어봐도 됨)

| # | 결론 |
|---|---|
| **D-7** | KR 경제값(SOW_RESIDUAL/SALVAGE, 원화) 글로벌 누수 → **출시 전 KR 전용 분리, 통화 일반화는 P2** (사용자 결정) |
| **D-8** | validator = `base` + 도메인 7 = **8개**. 8번째 = `finisher.py`(비육돈) (코드 확인) |
| **D-10** | 손실액(MSD) → **P2**(D-7과 함께 확정) |
| **D-11** | source_observations ↔ benchmarks 분리 → **MVP부터 분리**(작업 A에서 구현) |
| **D-12** | comparison_status 5단계, exact/compatible/normalized만 발화 → **구현됨**(작업 A) |
| **D-13** | fcr value_scale = **n/a**(문서 §2.2 'ratio'는 오기) → 확정·반영 |

---

## 요약 — 지금 당장 사용자가 할 일
1. **🔴 D-6**: 한돈팜스 공식 PDF 구하기 (KR verified의 유일한 블로커)
2. **🟡 D-4 + D-5**: US 적재 전 2개만 결정 (PWMFY 별도 / 사산율 가중방식)
3. **🔴 앵커마켓**: BR/VN 1차 수치 (출시 국가 KPI 작동시키려면)
4. **🟡 D-1, D-2**: NPD 후보돈 포함 / MSY 출하기준 — KR·US verified 전

나머지(D-3/D-9 EU·GB, TH/MX)는 해당 국가 적재 시점으로 미뤄도 됨.
