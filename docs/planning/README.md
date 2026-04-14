# Planning Docs

컨셉(제품 아이디어/브랜드)별로 폴더를 분리합니다. 공통 문서는 `common/`에 둡니다.

## 구조

```
docs/planning/
├── common/           ← 컨셉 공통 문서 (월간보고, 전사 리스크 등)
├── pigplancore/      ← PigPlanCORE 컨셉
└── README.md         ← 이 파일
```

## 컨셉별 인덱스

### common (공통)
- [2026-03_monthly-report.md](common/2026-03_monthly-report.md) — 2026년 3월 월간 보고
- [2026-04-05_risk-assessment.md](common/2026-04-05_risk-assessment.md) — PigOS 사업·개발 리스크 평가서

### pigplancore
- [2026-03-18_GlobalStrategy.html](pigplancore/2026-03-18_GlobalStrategy.html) — 글로벌 전략 심층분석 (HTML)
- [2026-03-18_GlobalStrategy_Content.md](pigplancore/2026-03-18_GlobalStrategy_Content.md) — 글로벌 전략 본문
- [2026-03-18_기능정의서_v0.1.md](pigplancore/2026-03-18_기능정의서_v0.1.md) — 기능 정의서 v0.1

## 새 컨셉 추가 규칙

1. `docs/planning/{concept-name}/` 폴더 생성 (소문자, 하이픈 구분)
2. 파일명은 `YYYY-MM-DD_주제.확장자` 형식
3. 이 README의 "컨셉별 인덱스"에 항목 추가
