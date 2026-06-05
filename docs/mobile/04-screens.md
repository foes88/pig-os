# 화면 목록 (웹 → Android 매핑)

## 네비게이션 구조

```
앱 진입
├── 로그인 (미인증)
│   ├── LoginScreen
│   └── OnboardingScreen
└── 메인 (인증 후)
    ├── DashboardScreen        ← BottomNav: 홈
    ├── SowsScreen             ← BottomNav: 모돈
    │   └── SowDetailScreen
    ├── RecordScreen           ← FAB or BottomNav: 기록
    ├── ChatScreen             ← BottomNav: AI
    └── MoreScreen             ← BottomNav: 더보기
        ├── KpiScreen
        ├── FinishersScreen
        ├── PigletsScreen
        └── SettingsScreen
```

---

## 화면별 상세

### LoginScreen
- 이메일 + 비밀번호 입력
- `POST /auth/login`
- 성공 → activeFarmId DataStore 저장 → DashboardScreen
- 첫 가입 → OnboardingScreen

---

### OnboardingScreen
- 3단계: 농장정보 → 관리자계정 → 확인
- `POST /onboarding/complete`
- 웹 `/onboarding` 그대로 구현

---

### DashboardScreen (홈)
- `GET /farms/{farm_id}/kpi/dashboard`
- 표시: PSY, NPD, 분만율, 폐사율
- AI Alert 카드 목록
- 생산 파이프라인 (교배→임신→분만→포유→이유)
- 웹 `src/app/(app)/page.tsx` 참고

---

### SowsScreen (모돈 목록)
- `GET /farms/{farm_id}/sows?status=&page=&per_page=`
- 상태 필터 탭 (전체/임신/포유/이유/건유)
- 귀표 번호 검색
- 무한 스크롤 (페이지네이션)
- FloatingActionButton → 모돈 등록
- 웹 `src/app/(app)/sows/page.tsx` 참고

### SowDetailScreen (모돈 상세)
- `GET /farms/{farm_id}/sows/{sow_id}`
- 번식 이력 타임라인 (교배→분만→이유 사이클)
- 웹 `src/app/(app)/sows/[id]/page.tsx` 참고

---

### RecordScreen (이벤트 기록)
탭 구성:
| 탭 | API |
|----|-----|
| 교배 | POST `/events/matings` |
| 분만 | POST `/events/farrowings` |
| 이유 | POST `/events/weanings` |
| 임신사고 | POST `/events/reproductive` |
| 도폐사 | POST `/sows/{sow_id}/cull` |

- 웹 `src/app/(app)/record/page.tsx` 참고
- 오프라인 우선: Room에 먼저 저장 → WorkManager 동기화

---

### ChatScreen (Q&A)
- `POST /farms/{farm_id}/chat/query`
- 자연어 질문 입력
- Rule Engine 기반 분석 결과 표시
- 추천 질문 칩
- 웹 `src/app/(app)/chat/page.tsx` 참고

---

### KpiScreen
- `GET /farms/{farm_id}/kpi/dashboard`
- `GET /farms/{farm_id}/kpi/psy`
- `GET /farms/{farm_id}/kpi/npd`
- KPI 카드 + Rule Engine 알림 목록
- 웹 `src/app/(app)/kpi/page.tsx` 참고

---

### FinishersScreen (비육돈)
- `GET/POST /farms/{farm_id}/finishers`
- 그룹 목록, 입식/출하 처리
- 웹 `src/app/(app)/finishers/page.tsx` 참고

---

### PigletsScreen (자돈)
- `GET/POST /farms/{farm_id}/piglets`
- 그룹 목록, 전출/판매 처리
- 웹 `src/app/(app)/piglets/page.tsx` 참고

---

## BottomNavigation 구성

```kotlin
sealed class BottomNavItem(val route: String, val label: Int, val icon: ImageVector) {
    object Dashboard  : BottomNavItem("dashboard",  R.string.nav_home,     Icons.Default.Home)
    object Sows       : BottomNavItem("sows",       R.string.nav_sows,     Icons.Default.Pets)
    object Record     : BottomNavItem("record",     R.string.nav_record,   Icons.Default.Edit)
    object Chat       : BottomNavItem("chat",       R.string.nav_ai,       Icons.Default.AutoAwesome)
    object More       : BottomNavItem("more",       R.string.nav_more,     Icons.Default.Menu)
}
```

---

## 웹 → Android 매핑 요약

| 웹 경로 | Android 화면 | 우선순위 |
|---------|-------------|---------|
| `/` | DashboardScreen | MVP |
| `/sows` | SowsScreen | MVP |
| `/sows/[id]` | SowDetailScreen | MVP |
| `/record` | RecordScreen | MVP |
| `/chat` | ChatScreen | MVP |
| `/kpi` | KpiScreen | MVP |
| `/finishers` | FinishersScreen | MVP |
| `/piglets` | PigletsScreen | MVP |
| `/login` | LoginScreen | MVP |
| `/onboarding` | OnboardingScreen | MVP |
| `/settings` | SettingsScreen | Phase 2 |
| `/notifications` | NotificationsScreen | Phase 2 |
