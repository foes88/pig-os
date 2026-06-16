# KPI 임계값 리서치 3자 비교분석

> 소스: ① Claude 리서치 ② GPT 리서치 ③ PigOS deep-research(진행중, 완료 시 추가).
> 목적: `default_metric_values` 시드 확정 전, 두(→세) 리서치의 합의/충돌을 정리하고 채택안 결정.
> 작성 2026-06-16.

---

## A. 두 리포트가 합의하는 것 (그대로 채택)
1. **메트릭 정의·방향 동일**: STILLBORN_RATE(above), BORN_ALIVE(below), PWM(above), WEANED_COUNT(below),
   WSI(above), RTS_RATE(above) + 기존 PSY/NPD/FR/FCR/SOW_MORTALITY.
2. **STILLBORN = 사산 + 미라**(둘 다 강조) → 화면에 "미라 포함" 명시 필수.
3. **WEANING_AGE = 이탈형(deviation)**, 단방향 아님 → LOW/HIGH 분리 또는 deviation 판정.
4. **산차·계절 보정은 v2**, v1은 전체평균 기준(둘 다 동일).
5. **저신뢰 국가 = VN(표본), KR(분리값 부재)** — 둘 다 동일하게 경고.
6. **없는 값 임의추정 금지**(GPT 명시 / Claude는 프록시+⚠ 라벨).

## B. 핵심 충돌 (결정 필요)

### B1. warning 산출 철학 — 가장 큰 차이
| | Claude | GPT |
|---|---|---|
| warning 기준 | 평균보다 **약간 나쁜 쪽**(버퍼), 국가 비교적 균일 | **국가 평균선 그대로** |
| 예: US 사산율 warning | 8% | 10.6%(=US 평균) |
| 예: BR 사산율 warning | 8.4% | 8.19%(=BR 평균) |
| 노이즈 | 낮음(평균 이하 일부만) | 높음(평균 미만 ~50% 농장이 warning) |
| 국가 보정 | 약함 | 강함 |

> **충돌 본질**: GPT는 "평균=warning"이라 국가맞춤이지만 **절반이 경고** → 알림 피로. Claude는 덜 울리지만 국가차 약함.
> **권고 절충**: 국가 평균은 **"평균 이하" INFO 라인**으로, **WARNING은 평균보다 한 단계 나쁜 점**(하위 25~33% 또는 평균−마진).
> → GPT의 국가별 앵커링 + Claude의 버퍼를 결합. (최종 수치는 deep-research 대조 후)

### B2. critical 값
- GPT: **실제 하위10% 분위**(US PWM 21.59, CN BORN_ALIVE 8.56) → 데이터 근거 강함.
- Claude: 둥근 값(18, 12) → 기억 쉬우나 근거 약함.
- **채택: GPT의 분위값 우선, 없으면 null**(둘 다 "없으면 비워라"에 동의).

### B3. target
- GPT: **PIC 글로벌 목표**(생존산자 15, 이유두수 14)로 통일 → 도전적.
- Claude: 국가 현실 목표(KR 생존산자 11) → 현실적.
- **채택: target은 GPT(글로벌 지향)로, 단 UI에 "국가평균 대비/글로벌목표 대비" 둘 다 표시**(B4 메타로 해결).

## C. GPT가 더 나은 점 — 반드시 흡수할 엔지니어링 (B4)
GPT는 임계값에 **출처/신뢰도 메타데이터**를 같이 저장하라고 함. 이게 핵심 개선:
- `confidence`: high / medium / low / unknown
- `is_proxy` + `proxy_type`(top10 / best_decile / cooperative / sample / global)
- `threshold_basis`: country_avg / poor_decile / PIC_intervention …
- `source` (기관/연도) 없는 숫자는 **저장 금지**
- **null = 해당 레벨 판정 skip** (없는 critical 억지로 안 만듦)
- RTS는 정의가 출처마다 달라(repeat service vs return to estrus) **하위 유형 분리 저장** 권장.

→ 현재 `default_metric_values`엔 이 컬럼들이 없음. **스키마 확장 필요**(아래 D).

## D. 스키마 영향 (default_metric_values 확장)
현재 컬럼: warning/critical/target/avg/top25/direction/unit. **추가 권장**:
```
confidence       VARCHAR(10)   -- high|medium|low|unknown
is_proxy         BOOLEAN       -- 프록시 사용 여부
proxy_type       VARCHAR(20)   -- top10|best_decile|cooperative|sample|global
threshold_basis  VARCHAR(40)   -- country_avg|poor_decile|pic_intervention|...
source_ref       VARCHAR(200)  -- 기관/연도
```
- `alert_direction`에 `deviation` 추가? → **권장 X**. WEANING_AGE는 `WEANING_AGE_LOW`(below)+`WEANING_AGE_HIGH`(above)
  **2행 분리**가 현재 엔진(단일 direction)과 더 잘 맞음.
- null 임계값 → 엔진이 해당 레벨 skip (이미 _severity_from_bench가 None 처리하나 재확인).

## E. 채택 결론 (deep-research 대조 전 잠정)
1. **메타데이터 컬럼 5종 추가**(C/D) — 가장 가치 큰 개선. 출처·신뢰도 추적.
2. **warning = 평균보다 한 단계 나쁜 점**(B1 절충), **평균 이하는 INFO**.
3. **critical = 하위분위(GPT) 우선, 없으면 null**.
4. **target = 글로벌(PIC) + UI에 국가평균 대비 병기**.
5. **WEANING_AGE = LOW/HIGH 2메트릭**.
6. **국가 적용도**: US/BR/CN 국가룰셋 / VN 프록시(표본) / KR 혼합+글로벌병기 (둘 다 합의).
7. 최종 수치는 **③ deep-research 대조 후** 확정 → 3자 일치하면 high, 2자 일치 medium, 1자뿐 low.

## F. 미해결 / 사람 결정
- B1 warning 마진(평균−몇%? 하위 몇 분위?) — 노이즈 vs 민감도 트레이드오프, **운영 정책 결정**.
- KR 값은 27년 노하우 최종 검수(둘 다 KR 저신뢰).
- RTS 하위유형 분리 저장 여부(데이터 모델 영향).
