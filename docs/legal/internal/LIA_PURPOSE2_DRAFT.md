<!-- STATUS: DRAFT_LAWYER_PENDING — 변호사 검토 전 초안. "LIA 완료·LI 확정" 아님. 게시·대외 제공 금지. 운영 실값·변호사 확인 후에만 확정. -->

# LIA — 목적② (PigSignal 익명·집계 통계 판매) 정당한 이익 평가 초안

> **DRAFT (RUN L, 2026-07-23).** 변호사 검토 전 초안 · 회사 실값 `[OPEN]` 미기입.
> 방법론: EU ICO 3-part LIA + BR ANPD LI 가이드 3단계. 안전장치는 `ANONYMIZATION_AND_RELEASE_STANDARD` 참조.
> 상태태그: `LEGAL_REQUIREMENT`/`OFFICIAL_GUIDANCE`/`DRAFT_GUIDANCE`/`CASE_OR_ENFORCEMENT`/`INTERNAL_POLICY_PROPOSAL`/`COUNSEL_CONFIRMATION_REQUIRED`.
> ⚠️ 목적②는 **동의 기반 아님**(D-01 국가별 분기 — EU/GB·BR=LI+고지+이의권). 본 LIA는 그 LI 근거의 문서화 초안.

---

## 0. 대상 처리 (Processing under assessment)
- **목적**: 이용자 농장의 생산성적·운영 데이터를 **비가역 익명화·집계**하여 산업 통계(PigSignal)를 산출하고 제3자에 제공(유상 포함).
- **개인정보 여부 전제**: 익명화가 `ANONYMIZATION_AND_RELEASE_STANDARD` 기준으로 성립하면 산출물은 개인정보 밖. **단 익명화 "행위 자체"의 처리 근거가 필요**(EDPB 02/2026 초안). 본 LIA는 그 익명화 처리 단계의 LI를 평가. `DRAFT_GUIDANCE`(EDPB 02/2026, 의견수렴 ~2026-10-30)
- 처리량·보유기간·파이프라인 구현 상태: `[OPEN — 운영 기입]`

## 1. 목적 테스트 (Purpose / 적법성)
- **식별된 정당한 이익**: (a) 산업 벤치마크·생산성 통계 제공이라는 회사의 상업적 이익, (b) 양돈 산업 전반의 생산성·질병 대응 개선이라는 제3자·공익. `INTERNAL_POLICY_PROPOSAL`
- **적법성**: 통계·벤치마크 제공은 그 자체로 위법 목적 아님. 단 **"유상 판매" 성질**이 형량 부담을 높임(KR 피그플랜 F2 리스크 참조). `COUNSEL_CONFIRMATION_REQUIRED`
- 판정(초안): 정당한 이익으로 식별 가능. 단 상업성으로 인해 3단계 형량에서 안전장치 강화 필요.

## 2. 필요성 테스트 (Necessity)
- **필요성**: 벤치마크·산업통계 산출에는 다수 농장 데이터의 집계가 본질적으로 필요. 개별 식별 데이터가 아니라 **집계·익명 산출물**로 목적 달성 가능 → 처리 범위를 익명·집계로 한정하는 것이 최소침해. `INTERNAL_POLICY_PROPOSAL`
- **덜 침해적 대안 검토**: (i) 동의 기반 — EU/GB·BR에서는 오히려 LI가 표준(동의 프레임이 자기구속·철회 리스크, D-01 근거). (ii) 완전 opt-in 표본 — 대표성·통계품질 저하. → 익명화 LI가 목적·품질·최소침해 균형상 적절. `COUNSEL_CONFIRMATION_REQUIRED`
- 판정(초안): 익명·집계 처리로 한정 시 필요성 충족. 식별 데이터 판매(목적⑤)와 **명확히 분리**되어야 함(⑤는 옵트인 D-02).

## 3. 형량 테스트 (Balancing) — 안전장치가 핵심
> ICO/ANPD: 정보주체 이익·권리·자유 대비 회사 이익 형량. **안전장치로 침해도 감축**.

**정보주체 측 (침해 요인)**
- 유상 판매 → 합리적 기대 밖일 수 있음(형량 불리 요인). `CASE_OR_ENFORCEMENT`(FTC §5·ANPD Meta 사건 경향)
- 대형 농장 편중 산업 → 집계에서도 재식별·역산 위험(지배율).

**안전장치 (침해 감축 — ANONYMIZATION_AND_RELEASE_STANDARD)**
- 직접식별자 삭제 → 준식별자 구간화 → 소수셀 억제 **k(기본10/세분20, `INTERNAL_POLICY_PROPOSAL` [D-05])** → 지배율 통제(p%-rule) → 이상치 제외. `INTERNAL_POLICY_PROPOSAL`
- 재식별 금지 공개 약속 + 수령자 재식별 금지 계약 구속(US de-id 3요건과 정합). `LEGAL_REQUIREMENT`(US)
- **이의권(Art.21)·제외요청 채널** — 접수 이후 배치에서 해당 농장 제외(기산출물은 존속 [D-04]). `LEGAL_REQUIREMENT`(EU/GB)
- 릴리스 원장 + 재식별 리스크 평가 기록(입증책임 회사). `INTERNAL_POLICY_PROPOSAL`

**형량 판정(초안)**: 위 안전장치 **전부 구현·증거화**되면 LI가 정보주체 권리에 우선한다고 주장 가능. **다만** (i) k값 통계검증 미완(D-05), (ii) 파이프라인 실제 구현 `[OPEN]`, (iii) FTC/ANPD의 익명화 주장 집행 경향 → **확정은 변호사 + 통계검증 후.** `COUNSEL_CONFIRMATION_REQUIRED`

---

## 4. 관할 변형

### EU / GB — Art.6(1)(f) + Art.21 + Art.89(1)
- LI 근거 + LIA 문서화 + Art.13/14 고지 + **Art.21 이의권 채널** 필수. **동의 체크박스 금지**(자기구속). `DRAFT_GUIDANCE`(EDPB 02/2026) + `OFFICIAL_GUIDANCE`(ICO 2025-03)
- GB: UK GDPR 동일 구조 + ICO 익명화 가이드(2025-03) 정합. 회원국별 언어 요건 `[COUNSEL]`.

### BR — Art.7 IX + ANPD LI 가이드 3단계
- LI + 고지 + 옵트아웃. **민감정보는 LI 불가** → 민감정보(있다면) 별도 근거. `OFFICIAL_GUIDANCE`(ANPD LI 가이드 2024-02)
- ANPD Meta 사건(LI 기반 처리 중지명령 전례) → 형량·안전장치 입증 강화. `CASE_OR_ENFORCEMENT`

### TH — §24(5) 정당한 이익
- PDPC 선례 미확립 → **고지 + 옵트아웃 병행 보수 운영**, 확정 전 유료·마케팅 게이트 유지(D-09). `COUNSEL_CONFIRMATION_REQUIRED`

### (참고) KR·US — LI 트랙 아님
- KR: 제58조의2 익명정보 법적용 제외 + 고지·제외요청(동의/이의권 프레임 아님). US: de-identified 제외(3요건) + 고지. 본 LIA(LI)는 EU/GB·BR·TH 대상.

---

## 5. 미결 `[OPEN]` / `[COUNSEL]` (확정 전 필수)
- `[OPEN — 운영]`: 처리량·보유기간·익명화 파이프라인 구현 상태·릴리스 원장 가동 여부.
- `[D-05]`: k값(기본10/세분20) 통계검증·확정.
- `[COUNSEL]`: 유상판매의 합리적 기대 형량 · FTC/ANPD 익명화 집행 리스크 · BR SCC/역할 · TH §24(5) 확정 · 회원국 언어.
- 관련: `HUMAN_INPUT_QUEUE.md`, `LAWYER_BRIEF.md`, `DECISION_REGISTER`(D-01·D-04·D-05).

## 6. 상태
**초안(DRAFT).** LIA "완료"·LI "확정" 아님. 변호사 검토 + 운영 실값(`[OPEN]`) 기입 + k값 통계검증 후에만 확정. 게시·대외 제공 금지.
