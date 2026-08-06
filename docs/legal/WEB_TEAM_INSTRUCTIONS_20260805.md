<!-- STATUS: 내부 지시서 (웹팀 하달용) · 2026-08-05 · 작성 근거: publish_candidate v1.0-rc + T1_RECHECK v1.3 -->

# 웹팀 지시 — 약관 페이지 준비 + footer 교체 (이번 주)

> 목적: 글로벌 약관 게시 준비 2건. **게시(publish)는 아직 하지 않는다** — 아래 게시 게이트 미충족.
> 근거: `docs/legal/publish_candidate/` (v1.0-rc, 8종), `docs/legal/reference/evidence/T1_RECHECK_20260804.md` (F-T1b).

---

## 지시 ① — publish_candidate 8종으로 약관 페이지 구성 (게시 보류)

**대상 소스** (`docs/legal/publish_candidate/`):
1. `PIGOS_MASTER_TERMS.md` — 마스터 이용약관
2. `PIGOS_GLOBAL_PRIVACY_NOTICE.md` — 글로벌 개인정보 처리방침
3. `ADDENDUM_US.md` / `ADDENDUM_EU.md` / `ADDENDUM_GB.md` / `ADDENDUM_BR.md` / `ADDENDUM_TH.md` / `ADDENDUM_VN.md` — 국가별 부속조항 6벌

**작업**:
- 위 8종을 `pigos.io/terms`·`/privacy` (및 국가별 부속 노출 구조)로 **페이지 빌드만** 한다.
- **문서 우선순위 구조를 UI에 반영**: 강행법규 > 국가별 부속조항 > 마스터 약관 > 개별정책 (마스터 제26조). 부속조항이 마스터보다 우선함이 사용자에게 명확해야 함 — T1 F-T1e 리스크(공개본이 "동의 기반"으로 자기구속) 해소의 전제.
- **staging/비공개 상태로만** 배포. 프로덕션 게시 금지.

**게시 게이트 (전원 충족 전 publish 금지)**:
- [ ] 문서 내 `[OPEN]` 빈칸 확정 (대행 대리인 EU/GB/TH·BR SCC 전문·손배상한·결제/환불·시행일 등)
- [ ] 변호사 검토 회신 반영
- [ ] 대표 최종 승인 + 시행일 확정
- [ ] PigSignal 목적②(익명·집계 유상제공) 처리는 게이트 충족 전 **OFF 유지**

---

## 지시 ② — footer 교체 (진교문/사업자번호/주소 블록)

**배경 (T1 F-T1b, 대표 확인 2026-08-05)**: 현행 `pigplan.io` 레거시 footer의 `CEO : Seung Hwan An` 표기는 **오류 → 제거**. 페이지 내 대표자 표기 자체 모순 해소.

**교체 대상**: pigplan.io 랜딩 공통 footer 템플릿 (privacy-policy.do 등에서 노출). *구 pigplan 레거시 소스 — 신규 PigOS 저장소 아님.*

**교체 후 회사정보 블록** (출처: publish_candidate 마스터약관 제25조):
```
상호: 주식회사 와이즈레이크 (WiseLake Inc.)
대표자: 진교문
주소: 경기도 안양시 동안구 동편로20번길 9, 스마트넷빌딩 3층
      (3rd Floor, Smartnet Building, 9 Dongpyeon-ro 20beon-gil, Dongan-gu, Anyang-si, Gyeonggi-do, Korea)
사업자등록번호: 768-87-02255
전화: +82-31-421-3418
전자우편: wiselake@wiselake.ai
```
- `CEO : Seung Hwan An` 문구 **제거**. 대표자 표기가 필요하면 **"진교문"으로 통일**.
- 완료 후 재캡처하여 `T1_RECHECK_20260804.md`에 완료 기록.

---

## ✅ 실값 확정됨 (대표 확인 2026-08-05) — footer 반영값

1. **전화번호**: **`+82-31-421-3418`로 전 문서 통일** (마스터약관 -3414 → -3418 정정 완료).
2. **개인정보 이메일 정본**: **`wiselake@wiselake.ai`** (publish_candidate 기준 유지). 기존 `wiselake@wiselake.co.kr`·`gyomoon@ezfarm.co.kr`은 **alias/forwarding으로 계속 수신**(진행 중 제외요청 유실 방지), 원장 통합. 새 주소만 남기고 기존 즉시 폐기 금지.

→ footer에 위 확정값(진교문 · +82-31-421-3418 · wiselake@wiselake.ai)으로 반영.
