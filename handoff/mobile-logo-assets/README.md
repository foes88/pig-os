# PigOS 모바일 로고/아이콘 전달 패키지

> 생성: 2026-06-15 · 원본: `Downloads/pigos_mobile_web_icon_package` + `src/public/logos`
> 브랜드: navy `#0D1B3E`, coral accent `#FF5A66`

mobile repo(wiselake/pigos-ios, wiselake/pigos-android)에 **그대로 드롭**해서 쓰는 패키지입니다.
이 폴더 자체는 PigOS 백엔드 repo에 보관용으로 둡니다. 아래 위치로 복사하세요.

---

## iOS — `ios/`

### 앱 아이콘
| 파일 | 넣을 위치 / 용도 |
|------|-----------|
| `AppIcon-1024.png` | `PigOS/Assets.xcassets/AppIcon.appiconset/` (라이트/기본) |
| `Contents.json` | `PigOS/Assets.xcassets/AppIcon.appiconset/` (기존 교체) |
| `AppIcon-dark-1024.png` | iOS 18 다크 앱아이콘 변형 (네이비 배경) — 선택 |
| `AppIcon-tinted-1024.png` | iOS 18 틴티드 변형 (흑백, Apple이 틴트) — 선택 |

- 1024×1024, **알파 없음(평탄화)** — App Store 요구사항 충족
- Xcode 14+ 단일 사이즈. 기본 2개만 넣으면 나머지 크기는 Xcode가 자동 생성
- 다크/틴티드까지 쓰려면 Contents.json에 `appearances` 항목 추가 후 3종 등록
- ⚠️ 원본 패키지의 `ios/apple-touch-icon-*.png`는 **PWA/Safari용** — 네이티브엔 쓰지 말 것

### 인앱 로고 (스플래시/헤더) — iOS는 SVG 불가 → imageset 제공
| 폴더 | 넣을 위치 |
|------|-----------|
| `PigOSLogo-light.imageset/` | `PigOS/Assets.xcassets/` 아래로 복사 → `Image("PigOSLogo-light")` |
| `PigOSLogo-dark.imageset/` | 어두운 배경용(흰색 로고) |

- 가로 로고 @1x(220pt)/2x/3x PNG 동봉 — Asset Catalog에 폴더째 드롭하면 끝

## Android — `android/`

minSdk 24라서 adaptive(API26+) + 레거시(API24/25) **둘 다** 필요합니다.

### 1) Adaptive foreground — `android/adaptive-foreground/`
밀도별 `mipmap-*/ic_launcher_foreground.png` (투명, 108dp 기준) → `app/src/main/res/` 아래 동일 경로로 복사.
- 배경은 이미 `colors.xml`에 `ic_launcher_background = #0D1B3E`로 설정돼 있음 (그대로 사용)
- 현재 `drawable/ic_launcher_foreground.xml`(플레이스홀더 벡터)를 PNG로 대체하려면:
  `mipmap-anydpi-v26/ic_launcher.xml`의 `foreground`/`monochrome`를
  `@drawable/ic_launcher_foreground` → `@mipmap/ic_launcher_foreground`로 바꾸고 placeholder 벡터 삭제
- **권장**: Android Studio → New → Image Asset → Foreground=투명 마크, Background=#0D1B3E 로 생성하면
  round/monochrome/모든 밀도를 IDE가 정확히 처리 (이 폴더의 투명 PNG를 소스로 사용)

### 2) Legacy mipmap (API24/25 폴백) — `android/legacy-mipmap/`
밀도별 `mipmap-*/ic_launcher.png` + `ic_launcher_round.png` (네이비 배경) → `app/src/main/res/` 아래로 복사.
- 현재 repo에 이 폴백이 **없음** → API26 미만 기기에서 아이콘 누락 방지용으로 추가 필요

> ⚠️ 이 PNG들은 정적 생성물입니다. **Gradle 빌드 검증은 안 했으니** 머지 전 Android Studio에서
> 빌드 + 런처 미리보기 확인 필수. 가능하면 Image Asset Studio 방식을 우선.

## 인앱 로고 (스플래시/헤더) — `in-app/`

| 파일 | 용도 |
|------|------|
| `pigos-logo-horizontal-light.svg` | 밝은 배경 위 가로 로고 |
| `pigos-logo-horizontal-dark.svg` | 어두운 배경 위 가로 로고(흰색) |
| `pigos-symbol-light.svg` / `-dark.svg` | 심볼만 (좁은 영역) |

- iOS: SVG는 SF Symbols 아님 → PDF로 변환해 Assets에 넣거나 SVGKit/PNG 사용
- Android: `app/src/main/res/drawable/`에 VectorDrawable로 변환(Android Studio Vector Asset) 후 사용

---

## 빠른 체크리스트
- [ ] iOS: AppIcon-1024.png + Contents.json 복사
- [ ] Android: adaptive foreground 밀도별 복사 (또는 Image Asset Studio 재생성)
- [ ] Android: legacy mipmap 복사 (API24/25 폴백)
- [ ] Android Studio 빌드 + 런처 아이콘 미리보기 확인
- [ ] 인앱 스플래시/헤더 로고 적용
