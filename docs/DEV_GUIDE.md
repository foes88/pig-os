# PigOS 개발 가이드
> 이 문서 하나로 개발 환경 세팅부터 MVP P0 구현까지 가능하게 작성됨
> 최종 갱신: 2026-06-19

---

## 목차

1. [기술 스택](#1-기술-스택)
2. [로컬 환경 세팅](#2-로컬-환경-세팅)
3. [프로젝트 구조](#3-프로젝트-구조)
4. [개발 규칙](#4-개발-규칙)
5. [MVP P0 구현 태스크](#5-mvp-p0-구현-태스크)
6. [API 엔드포인트 목록](#6-api-엔드포인트-목록)
7. [DB 모델 목록](#7-db-모델-목록)
8. [프론트엔드 페이지 목록](#8-프론트엔드-페이지-목록)
9. [테스트 실행](#9-테스트-실행)
10. [배포](#10-배포)

---

## 1. 기술 스택

| 영역 | 기술 |
|------|------|
| **백엔드** | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic |
| **DB** | PostgreSQL 16 (로컬), Supabase (프로덕션) |
| **캐시/큐** | Redis 7, ARQ (백그라운드 작업) |
| **프론트엔드** | Next.js 15 (App Router), TypeScript, Tailwind CSS 4 |
| **상태관리** | Zustand (클라이언트), TanStack Query (서버) |
| **폼/검증** | React Hook Form + Zod |
| **인증** | JWT (Access 15분 + Refresh 7일) |
| **컨테이너** | Docker + docker-compose |
| **다국어** | next-intl (en/ko/zh/es/vi) |

---

## 2. 로컬 환경 세팅

### 2-1. 사전 조건

- Docker Desktop 설치
- Node.js (`.nvmrc` 버전)
- Python 3.12+
- `uv` 패키지 매니저 (`pip install uv`)

### 2-2. 백엔드 실행

```bash
# 1. DB + Redis 컨테이너 시작
docker compose up -d db redis

# 2. Python 의존성 설치
cd api
uv pip install -e ".[dev]"   # 또는 uv pip install -r requirements.txt

# 3. 환경변수 설정
cp .env.example .env
# .env 에서 DATABASE_URL, SECRET_KEY 확인

# 4. DB 마이그레이션
alembic upgrade head

# 5. 서버 실행 (포트 8000)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**API 문서**: http://localhost:8000/docs (Swagger UI)

### 2-3. 프론트엔드 실행

```bash
cd src

# 1. 패키지 설치
npm install

# 2. 환경변수 설정
cp .env.example .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000

# 3. 개발 서버 실행 (포트 3000)
npm run dev
```

**앱**: http://localhost:3000

### 2-4. 환경변수 목록

**백엔드 (`api/.env`)**
```
DATABASE_URL=postgresql+asyncpg://pigos:pigos@localhost:5432/pigos
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=your-32-char-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
ENVIRONMENT=development
# 선택사항
ANTHROPIC_API_KEY=   # AI 인사이트 기능
FCM_PROJECT_ID=      # 푸시 알림
SENTRY_DSN=          # 에러 모니터링
```

**프론트엔드 (`src/.env.local`)**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 2-5. DB 마이그레이션 명령어

```bash
cd api

alembic current                              # 현재 버전 확인
alembic upgrade head                         # 최신으로 적용
alembic revision --autogenerate -m "설명"    # 모델 변경 후 마이그레이션 생성
alembic downgrade -1                         # 한 버전 롤백
```

---

## 3. 프로젝트 구조

```
C:/dev/PigOS/
├── api/                          ← FastAPI 백엔드
│   └── app/
│       ├── main.py               ← 앱 진입점 (prefix: /api/v1)
│       ├── routers/base/         ← 라우터 22개
│       ├── services/             ← 비즈니스 로직 17개
│       │   └── event_service.py  ← 핵심 (교배/분만/이유/자돈 처리)
│       ├── validators/           ← 순수 검증 함수
│       ├── db/models/            ← SQLAlchemy 모델
│       └── schemas/              ← Pydantic 요청/응답 모델
│
├── src/                          ← Next.js 프론트엔드
│   └── app/
│       ├── (app)/                ← 인증 후 화면
│       │   ├── sows/             ← 모돈
│       │   ├── farrowing/        ← 분만 입력
│       │   ├── record/           ← 빠른 입력
│       │   └── reports/          ← 보고서
│       └── (auth)/               ← 로그인/회원가입
│   └── lib/api/endpoints/        ← API 호출 함수
│   └── components/               ← 공통 컴포넌트
│
├── alembic/                      ← DB 마이그레이션
└── docs/                         ← 개발 문서
    ├── DEV_GUIDE.md              ← 이 파일
    ├── VALIDATION_SPEC.md        ← 검증 기준서 (P0/P1/P2)
    └── MVP_SCOPE.md              ← MVP 범위 정의
```

### 핵심 파일 경로

| 역할 | 파일 경로 |
|------|----------|
| 이벤트 서비스 (핵심) | `api/app/services/event_service.py` |
| 모돈 라우터 | `api/app/routers/base/sows.py` |
| 이벤트 라우터 | `api/app/routers/base/events.py` |
| 비육돈 라우터 | `api/app/routers/base/finishers.py` |
| 모돈 모델 | `api/app/db/models/sow.py` |
| 이벤트 모델 | `api/app/db/models/events.py` |
| Validators | `api/app/validators/` |
| 이벤트 API 호출 | `src/lib/api/endpoints/events.ts` |
| 분만 입력 페이지 | `src/app/(app)/farrowing/page.tsx` |
| 빠른 입력 드로어 | `src/components/QuickInputDrawer.tsx` |

---

## 4. 개발 규칙

### 백엔드 패턴

```python
# 라우터 → 서비스 → validator 순서
@router.post("/matings")
async def create_mating(req: MatingCreate, db: DbDep, user: CurrentUser):
    return await event_service.record_mating(db=db, farm_id=..., req=req, user_id=user.id)

# validator는 순수 함수 (DB 없음)
# api/app/validators/xxx.py
def validate_xxx(*, field1, field2) -> None:
    if 조건:
        raise ValidationError("메시지")

# event_service에서 validator 호출 후 DB 저장
```

### 프론트엔드 패턴

```typescript
// API 호출: lib/api/endpoints/ 에 함수 정의
export const eventsApi = {
  recordMating: (farmId: string, data: MatingCreate) =>
    apiClient.post(`/farms/${farmId}/events/matings`, data),
};

// 폼: React Hook Form + Zod
const schema = z.object({ ... });
const { register, handleSubmit } = useForm({ resolver: zodResolver(schema) });

// 서버 상태: TanStack Query
const { data } = useQuery(queryKeys.sows.list(farmId), () => sowsApi.list(farmId));
const mutation = useMutation({ mutationFn: eventsApi.recordMating });
```

### 공통 규칙

- **멀티테넌트**: 모든 DB 쿼리에 `farm_id` 필터 필수
- **소프트 삭제**: `deleted_at` 컬럼으로 처리 (실제 삭제 금지)
- **감사 로그**: CUD 작업은 `_audit()` 헬퍼로 기록
- **월마감 잠금**: 수정/삭제 전 `_ensure_period_unlocked()` 호출
- **DB 커밋**: `db.commit()`은 라우터 레이어에서 (서비스에서 하지 않음)

---

## 5. MVP P0 구현 태스크

> 검증 상세 기준: `docs/VALIDATION_SPEC.md` 참조
> 우선순위: 백엔드 검증 완성 → 프론트 Zod schema → 보고서

### 5-A. 백엔드 구현 (13개)

#### [P0-BE-1] validate_weaning() 호출 연결

**파일**: `api/app/services/event_service.py`

현재 `weaning.py`에 이유두수 공식 함수가 있지만 `event_service.py`에서 호출하지 않음.

```python
# 상단 import 추가
from app.validators.weaning import validate_weaning

# record_weaning() 안에서 _calc_piglet_adjustments 이후 추가
foster_in, foster_out, deaths = await _calc_piglet_adjustments(db, farrowing.id)
nursing_head = farrowing.nursing_head or farrowing.born_alive
validate_weaning(
    weaned=req.weaned_count,
    nursing_head=nursing_head,
    deaths=deaths,
    transfers_out=foster_out,
    transfers_in=foster_in,
)
```

공식: `weaned == nursing_head - deaths - transfers_out + transfers_in`  
출처: `DataValidationChk.java` L747~752

---

#### [P0-BE-2] 이유체중 범위 검증

**파일**: `api/app/services/event_service.py` — `record_weaning()` 안

```python
if req.avg_weaning_weight_kg is not None:
    if not (2.0 <= req.avg_weaning_weight_kg <= 12.0):
        raise ValidationError(
            f"이유체중 {req.avg_weaning_weight_kg}kg은 유효 범위(2~12kg)를 벗어납니다"
        )
```

---

#### [P0-BE-3] 양자 거울 레코드 자동생성

**파일**: `api/app/services/event_service.py` — `record_piglet_event()` 안

FOSTER_OUT 입력 시 target_sow에 FOSTER_IN 자동 생성 (양방향 보장).  
없으면 nursing_head 집계가 한쪽만 반영됨.

```python
# event 저장 직후 추가
if req.event_type in ("FOSTER_IN", "FOSTER_OUT"):
    mirror_type = "FOSTER_IN" if req.event_type == "FOSTER_OUT" else "FOSTER_OUT"
    target_farrowing = await db.scalar(
        select(Farrowing)
        .where(
            Farrowing.sow_id == req.target_sow_id,
            Farrowing.deleted_at.is_(None),
        )
        .order_by(Farrowing.farrowing_date.desc())
        .limit(1)
    )
    if target_farrowing:
        db.add(PigletEvent(
            farm_id=farm_id,
            farrowing_id=target_farrowing.id,
            sow_id=req.target_sow_id,
            event_date=req.event_date,
            event_type=mirror_type,
            piglet_count=req.piglet_count,
            target_sow_id=sow.id,
            target_farrowing_id=farrowing.id,
            notes=f"auto-mirror:{event.id}",
            created_by=user_id,
        ))
```

출처: `MdYangjaWrMapper.xml` L383~398

---

#### [P0-BE-4] nursing_head 컬럼 추가 + 자동계산

**파일 1**: `api/app/db/models/events.py` — Farrowing 모델

```python
nursing_head: Mapped[int | None] = mapped_column(Integer, comment="포유개시두수")
```

**파일 2**: `api/app/services/event_service.py` — `record_farrowing()` 안

```python
# farrowing 객체 생성 시 nursing_head 초기값 설정
farrowing = Farrowing(
    ...
    nursing_head=req.born_alive,  # 양자이동 발생 시 piglet_event로 갱신
)
```

**마이그레이션**: 컬럼 추가 후 `alembic revision --autogenerate -m "Add nursing_head to farrowing"`

출처: `MdChildbirthWrMapper.xml` L40~54

---

#### [P0-BE-5] 자돈 age_days 자동계산

**파일 1**: `api/app/db/models/events.py` — PigletEvent 모델

```python
age_days: Mapped[int | None] = mapped_column(Integer, comment="자돈 일령")
```

**파일 2**: `api/app/services/event_service.py` — `record_piglet_event()` 안

```python
event = PigletEvent(
    ...
    age_days=(req.event_date - farrowing.farrowing_date).days,
)
```

**마이그레이션**: `alembic revision --autogenerate -m "Add age_days to piglet_event"`

출처: `MdPjadongDiedWrMapper.xml` L342~346

---

#### [P0-BE-6] validate_farrowing() 인자 완성

**파일**: `api/app/services/event_service.py`

현재 avg_birth_weight_kg, 암수 인자를 전달하지 않아 체크 안 됨.

```python
# record_farrowing() 안
validate_farrowing(
    total_born=req.total_born,
    born_alive=req.born_alive,
    stillborn=req.stillborn,
    mummified=req.mummified,
    avg_birth_weight_kg=req.avg_birth_weight_kg,    # ← 추가
    male=getattr(req, "born_alive_male", None),      # ← 추가
    female=getattr(req, "born_alive_female", None),  # ← 추가
)

# update_farrowing() 안에도 동일하게 추가
```

---

#### [P0-BE-7] 동일 날짜 중복 교배 방지

**파일**: `api/app/services/event_service.py` — `record_mating()` 안

```python
# 교배 가능 상태 검증 이후에 추가
dup = await db.scalar(
    select(Mating).where(
        Mating.sow_id == sow.id,
        Mating.mating_date == req.mating_date,
        Mating.deleted_at.is_(None),
    )
)
if dup:
    raise ConflictError("해당 날짜에 이미 교배 기록이 있습니다")
```

---

#### [P0-BE-8] 웅돈 ACTIVE 상태 확인

**파일**: `api/app/services/event_service.py` — `record_mating()` 안

```python
if req.boar_id:
    boar = await db.get(Boar, req.boar_id)
    if not boar:
        raise NotFoundError("웅돈을 찾을 수 없습니다")
    if boar.status != "ACTIVE":
        raise ValidationError(
            f"웅돈 {boar.ear_tag}은 현재 {boar.status} 상태로 교배에 사용할 수 없습니다"
        )
```

---

#### [P0-BE-9] 교배 시 웅돈 순서 인자 전달

**파일**: `api/app/services/event_service.py` — `record_mating()` 안

```python
# 현재
validate_mating(sow_status=sow.status)

# 변경
validate_mating(
    sow_status=sow.status,
    boar_1=req.boar_id,
    boar_2=getattr(req, "boar_id_2", None),
    boar_3=getattr(req, "boar_id_3", None),
)
```

---

#### [P0-BE-10] 임신 중 도폐사 시 사유 필수

**파일**: `api/app/services/event_service.py` — `record_reproductive_event()` 또는 도폐사 처리 함수 안

```python
if sow.status == "PREGNANT" and req.removal_type in ("CULLED", "DEAD"):
    if not req.notes:
        raise ValidationError("임신돈 도폐사 시 사유(notes)를 입력해야 합니다")
```

---

#### [P0-BE-11] validators/finisher.py 신규 생성

**파일**: `api/app/validators/finisher.py` (신규)

```python
"""
비육돈 그룹 검증.
출처: PigPlan DataValidationChk.java L943~1047, UdMoveinWr.jsp
"""
from app.validators.base import ValidationError

MIN_ENTRY_WEIGHT_KG = 5.0
MAX_ENTRY_WEIGHT_KG = 50.0
MAX_EXIT_WEIGHT_KG  = 200.0


def validate_finisher_entry(
    *, entry_count: int, avg_entry_weight_kg: float | None = None
) -> None:
    if entry_count < 1:
        raise ValidationError("입식두수는 1두 이상이어야 합니다")
    if avg_entry_weight_kg is not None:
        if not (MIN_ENTRY_WEIGHT_KG <= avg_entry_weight_kg <= MAX_ENTRY_WEIGHT_KG):
            raise ValidationError(
                f"입식체중은 {MIN_ENTRY_WEIGHT_KG}~{MAX_ENTRY_WEIGHT_KG}kg 범위여야 합니다"
            )


def validate_finisher_event_count(
    *, action_count: int, remaining_head: int, label: str = "두수"
) -> None:
    """폐사/출하/전출 두수 ≤ 잔여두수"""
    if action_count < 1:
        raise ValidationError(f"{label}는 1두 이상이어야 합니다")
    if action_count > remaining_head:
        raise ValidationError(
            f"{label} {action_count}두가 잔여두수 {remaining_head}두를 초과합니다"
        )


def validate_finisher_not_shipped(*, shipped_at) -> None:
    if shipped_at is not None:
        raise ValidationError("출하 완료 그룹에는 추가 이벤트를 등록할 수 없습니다")


def validate_finisher_exit_weight(
    *, avg_exit_weight_kg: float, avg_entry_weight_kg: float | None = None
) -> None:
    if avg_exit_weight_kg > MAX_EXIT_WEIGHT_KG:
        raise ValidationError(
            f"출하체중이 최대 {MAX_EXIT_WEIGHT_KG}kg을 초과합니다"
        )
    if avg_entry_weight_kg and avg_exit_weight_kg <= avg_entry_weight_kg:
        raise ValidationError("출하체중은 입식체중보다 커야 합니다")


def calc_remaining_head(group) -> int:
    """잔여두수 = 입식 + 전입 - 폐사 - 전출 - 출하"""
    return (
        group.entry_count
        + (group.total_transfers_in or 0)
        - (group.total_deaths or 0)
        - (group.total_transfers_out or 0)
        - (group.total_shipped or 0)
    )
```

---

#### [P0-BE-12] 비육돈 잔여두수 검증 연결

**파일**: `api/app/routers/base/finishers.py`

```python
from app.validators.finisher import (
    validate_finisher_entry,
    validate_finisher_event_count,
    validate_finisher_not_shipped,
    validate_finisher_exit_weight,
    calc_remaining_head,
)

# 입식 라우터에서
validate_finisher_entry(
    entry_count=req.head_count_in,
    avg_entry_weight_kg=req.avg_entry_weight_kg,
)

# 폐사 등록 라우터에서
remaining = calc_remaining_head(group)
validate_finisher_not_shipped(shipped_at=group.shipped_at)
validate_finisher_event_count(action_count=req.head_count, remaining_head=remaining, label="폐사두수")

# 출하 라우터에서
validate_finisher_not_shipped(shipped_at=group.shipped_at)
validate_finisher_event_count(action_count=req.head_count_out, remaining_head=remaining, label="출하두수")
if req.avg_exit_weight_kg:
    validate_finisher_exit_weight(
        avg_exit_weight_kg=req.avg_exit_weight_kg,
        avg_entry_weight_kg=group.avg_entry_weight_kg,
    )
```

---

#### [P0-BE-13] 분만 수정 시 avg_birth_weight 재검증

**파일**: `api/app/services/event_service.py` — `update_farrowing()` 안

```python
# 기존 validate_farrowing 호출에 인자 추가
validate_farrowing(
    total_born=f.total_born,
    born_alive=f.born_alive,
    stillborn=f.stillborn,
    mummified=f.mummified,
    avg_birth_weight_kg=f.avg_birth_weight_kg,  # ← 추가
)
```

---

### 5-B. 프론트엔드 Zod Schema (7개)

> 위치: 각 폼 컴포넌트 상단에 선언
> 패턴: `const schema = z.object({...}); useForm({ resolver: zodResolver(schema) })`

#### [P0-FE-1] 분만 폼 (+ 실시간 자동계산)

```typescript
// src/app/(app)/farrowing/page.tsx 또는 분만 입력 컴포넌트
const farrowingSchema = z.object({
  farrowing_date: z.string().refine(d => new Date(d) <= new Date(), {
    message: "분만일은 오늘 이전이어야 합니다",
  }),
  total_born: z.number().int().min(0).max(35),
  born_alive: z.number().int().min(0).max(35),
  stillborn: z.number().int().min(0).max(25),
  mummified: z.number().int().min(0).max(25),
  avg_birth_weight_kg: z.number().min(0).max(3.0).optional(),
  born_alive_male: z.number().int().min(0).optional(),
  born_alive_female: z.number().int().min(0).optional(),
}).refine(d => d.total_born === d.born_alive + d.stillborn + d.mummified, {
  message: "총산 = 실산 + 사산 + 미라 이어야 합니다",
  path: ["total_born"],
}).refine(
  d => d.born_alive_male == null || d.born_alive_female == null ||
       d.born_alive_male + d.born_alive_female === d.born_alive,
  { message: "암수 합계가 실산과 일치해야 합니다", path: ["born_alive_male"] }
);

// UI에서 실시간 자동계산 표시 (watch 사용)
// total_born = born_alive + stillborn + mummified  → 자동 표시
// nursing_head = born_alive                        → 초기값 표시
```

#### [P0-FE-2] 이유 폼

```typescript
const weaningSchema = z.object({
  weaning_date: z.string().refine(d => new Date(d) <= new Date(), {
    message: "이유일은 오늘 이전이어야 합니다",
  }),
  weaned_count: z.number().int().min(0),
  avg_weaning_weight_kg: z.number().min(2.0).max(12.0).optional(),
});
// UI: weaned_count === 0 이면 confirm 팝업
```

#### [P0-FE-3] 교배 폼

```typescript
const matingSchema = z.object({
  mating_date: z.string().refine(d => new Date(d) <= new Date(), {
    message: "교배일은 오늘 이전이어야 합니다",
  }),
  boar_id: z.string().uuid("웅돈을 선택해주세요"),
  boar_id_2: z.string().uuid().optional(),
  boar_id_3: z.string().uuid().optional(),
});
```

#### [P0-FE-4] 자돈 이벤트 폼 (양자/폐사)

```typescript
const pigletEventSchema = z.object({
  event_type: z.enum(["FOSTER_IN", "FOSTER_OUT", "DEATH"]),
  event_date: z.string().refine(d => new Date(d) <= new Date()),
  piglet_count: z.number().int().min(1).max(25),
  target_sow_id: z.string().uuid().optional(),
}).refine(
  d => d.event_type === "DEATH" || !!d.target_sow_id,
  { message: "양자 이동 시 대상 모돈을 선택해야 합니다", path: ["target_sow_id"] }
);
```

#### [P0-FE-5] 도폐사 폼

```typescript
const cullSchema = z.object({
  removal_type: z.enum(["CULLED", "DEAD", "SOLD", "TRANSFER"]),
  removal_date: z.string().refine(d => new Date(d) <= new Date(), {
    message: "도폐사일은 오늘 이전이어야 합니다",
  }),
  body_weight_kg: z.number().min(0).max(99999).optional(),
  notes: z.string().optional(),
});
```

#### [P0-FE-6] 모돈 전입 폼

```typescript
const sowSchema = z.object({
  ear_tag: z.string().min(1, "개체번호는 필수입니다"),
  entry_date: z.string().refine(d => new Date(d) <= new Date(), {
    message: "전입일은 오늘 이전이어야 합니다",
  }),
  parity: z.number().int().min(0).max(20).default(0),
  entry_type: z.enum(["GILT", "PURCHASE", "TRANSFER", "BORN"]),
});
```

#### [P0-FE-7] 비육돈 입식/출하 폼

```typescript
const finisherEntrySchema = z.object({
  group_code: z.string().min(1).max(30),
  start_date: z.string().refine(d => new Date(d) <= new Date()),
  head_count_in: z.number().int().min(1, "입식두수는 1두 이상이어야 합니다"),
  avg_entry_weight_kg: z.number().min(5).max(50).optional(),
});

const finisherShipSchema = z.object({
  end_date: z.string().refine(d => new Date(d) <= new Date()),
  head_count_out: z.number().int().min(1),
  avg_exit_weight_kg: z.number().min(0).max(200).optional(),
});
```

---

### 5-C. MVP 보고서 5개

> 위치: `src/app/(app)/reports/` 하위 폴더  
> API: `api/app/routers/base/reports.py` + `api/app/services/report_service.py`

| # | 보고서명 | URL | 핵심 데이터 |
|---|---------|-----|------------|
| 1 | 모돈 현재 상태표 | `/reports/sow-status` | 상태별 두수, 모돈 목록 (GILT/PREGNANT/LACTATING/OPEN/ACCIDENT) |
| 2 | 번식 성적 요약 | `/reports/reproduction` | WSI, NSY, PSY, 분만율, 이유두수 KPI (기간 선택) |
| 3 | 분만·포유·이유 성적표 | `/reports/farrowing` | 총산·실산·이유두수·이유일령 산차별/기간별 |
| 4 | 도폐사/포유폐사 리포트 | `/reports/mortality` | 원인별 도폐사 두수, 포유 중 폐사율 |
| 5 | 데이터 오류/누락 리포트 | `/reports/data-quality` | 날짜 역전·두수 불일치·상태 오류·입력 누락 모돈 목록 |

---

## 6. API 엔드포인트 목록

모든 엔드포인트 prefix: `/api/v1`  
인증: `Authorization: Bearer <access_token>` (pilot-signups 제외)

| 라우터 | Prefix | 주요 엔드포인트 |
|--------|--------|----------------|
| auth | `/auth` | POST /register, /login, /refresh, /logout, GET /me |
| farms | `/farms` | GET /, GET /{id}, PATCH /{id} |
| **sows** | `/farms/{farm_id}/sows` | GET, POST, GET /{id}, PATCH /{id}, POST /{id}/cull |
| **events** | `/farms/{farm_id}/events` | POST /matings, /farrowings, /weanings, /piglet-events |
| kpi | `/farms/{farm_id}/kpi` | GET /summary, /dashboard, /trend |
| **finishers** | `/farms/{farm_id}/finishers` | GET, POST, PATCH /{id}, POST /{id}/ship |
| **boars** | `/farms/{farm_id}/boars` | GET, POST, PATCH /{id} |
| piglets | `/farms/{farm_id}/piglets` | GET, POST |
| reports | `/farms/{farm_id}/reports` | GET /reproduction, /daily, /grow-finish |
| alerts | `/farms/{farm_id}/alerts` | GET /rules, GET /active |
| tasks | `/farms/{farm_id}/tasks` | GET, POST, PATCH /{id}/status |
| notifications | `/notifications` | GET, POST /mark-read |
| members | `/farms/{farm_id}/members` | GET, PATCH /{id}/role |
| chat | `/farms/{farm_id}/chat` | POST /ask |

---

## 7. DB 모델 목록

**핵심 모델** (`api/app/db/models/`)

| 파일 | 모델 | 설명 |
|------|------|------|
| `platform.py` | User, Organization, Farm, UserFarm | 멀티테넌트 기반 |
| `sow.py` | **Sow**, BreedingCycle, PigletGroup | 모돈 핵심 |
| `events.py` | **Mating**, **Farrowing**, **Weaning**, **PigletEvent** | 번식 이벤트 핵심 |
| `health.py` | HealthEvent, **Removal**, FeedRecord | 도폐사/건강 |
| `ops.py` | Task, Notification, **PeriodLock**, KpiSnapshot | 운영 |
| `config.py` | FarmConfig, ComplianceProfile, RegionDefault | 설정 |

**Sow 상태값** (`sow.status`)
```
GILT → PREGNANT → LACTATING → OPEN → (반복)
                     ↓
                  ACCIDENT
                     
종료: CULLED / DEAD / SOLD / TRANSFER
```

---

## 8. 프론트엔드 페이지 목록

| 경로 | 설명 | 상태 |
|------|------|------|
| `/` | 대시보드 (KPI 요약, 최근 이벤트) | 구현됨 |
| `/sows` | 모돈 목록 | 구현됨 |
| `/sows/[id]` | 모돈 상세 + 번식 이력 | 구현됨 |
| `/farrowing` | 분만 입력 | 구현됨 (Zod 추가 필요) |
| `/record` | 빠른 입력 드로어 | 구현됨 (Zod 추가 필요) |
| `/finishers` | 비육돈 그룹 목록 | 구현됨 |
| `/boars` | 웅돈 목록 | 구현됨 |
| `/reports/reproduction` | 번식 보고서 | 구현됨 |
| `/reports/sow-status` | 모돈 현재 상태표 | **추가 필요** |
| `/reports/farrowing` | 분만 성적표 | **추가 필요** |
| `/reports/mortality` | 도폐사 리포트 | **추가 필요** |
| `/reports/data-quality` | 데이터 오류 리포트 | **추가 필요** |
| `/kpi` | KPI 대시보드 | 구현됨 |
| `/alerts` | 알림 규칙 | 구현됨 |
| `/tasks` | 작업 관리 | 구현됨 |
| `/chat` | AI Q&A | 구현됨 |
| `/settings` | 농장 설정 | 구현됨 |

---

## 9. 테스트 실행

```bash
# 백엔드
cd api
pytest tests/                    # 전체
pytest tests/test_events.py -v   # 이벤트 테스트만

# 프론트엔드 유닛
cd src
npm run test:run                  # 전체
npm run test -- --watch           # 감시 모드

# E2E
npm run test:e2e                  # 로컬
npm run test:e2e:live             # 프로덕션 대상
```

---

## 10. 배포

### 로컬 → 프로덕션

```bash
# 1. 코드 tar 압축
tar --exclude='.env*' --exclude='node_modules' --exclude='__pycache__' \
    -czf pigos.tar.gz .

# 2. 서버 전송
scp pigos.tar.gz ubuntu@52.78.65.6:/home/ubuntu/

# 3. 서버에서 실행
ssh ubuntu@52.78.65.6
cd /home/ubuntu && tar -xzf pigos.tar.gz -C pigos/
cd pigos
sudo docker compose -f docker-compose.prod.yml -f docker-compose.deploy.yml \
    up -d --build web api worker
```

### 도메인 구조

| 도메인 | 서비스 | 포트 |
|--------|--------|------|
| app.pigos.io | Next.js | 3010 |
| api.pigos.io | FastAPI | 8010 |

---

## 관련 문서

| 문서 | 경로 | 내용 |
|------|------|------|
| 검증 기준서 | `docs/VALIDATION_SPEC.md` | 모돈/웅돈/비육돈 validation P0/P1/P2 |
| MVP 범위 | `docs/MVP_SCOPE.md` | MVP 구현 범위 확정 |
| 아키텍처 | `CLAUDE.md` | 전체 아키텍처 + 개발 프로토콜 |
