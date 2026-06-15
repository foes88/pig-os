# PigOS 모바일 로고/아이콘 전달 패키지 (v2 — 공식 로고 기준)

> 생성: 2026-06-15 · **권위 소스: `C:\dev\pigos-landing\public`** (PigOS Symbol 09)
> 스타일: 네이비 `#0D1B3E` 배경 + 흰색 심볼 + 코랄 `#FF5A66` 중앙 (= 공식 android-chrome 아이콘과 동일)
>
> ⚠️ 이전 패키지(밝은 배경/Downloads 출처)는 **폐기**됨. 이 v2만 사용.

심볼은 공식 `pigos-symbol-color.svg` 좌표를 1024 네이티브에서 정밀 렌더(4x 슈퍼샘플)했고,
가로 로고는 pigos-landing의 공식 PNG를 사용했습니다.

---

## iOS — `ios/`

### 앱 아이콘
| 파일 | 위치 / 용도 |
|------|-----------|
| `AppIcon-1024.png` | `Assets.xcassets/AppIcon.appiconset/` (네이비+흰 심볼, 불투명) |
| `Contents.json` | 같은 폴더 (기존 교체) |
| `AppIcon-dark-1024.png` | iOS 18 다크 변형 — 선택 |
| `AppIcon-tinted-1024.png` | iOS 18 틴티드(흰 심볼/투명) — 선택 |

- 1024 단일, 알파 없음 → Xcode 14+가 나머지 자동 생성

### 인앱 로고 (스플래시/헤더)
| 폴더 | 위치 |
|------|------|
| `PigOSLogo-light.imageset/` | `Assets.xcassets/` → `Image("PigOSLogo-light")` |
| `PigOSLogo-dark.imageset/` | 어두운 배경용 |

## Android — `android/`

minSdk 24 → adaptive(26+) + 레거시(24/25) 둘 다.

### Adaptive — `android/adaptive-foreground/`
- 밀도별 `mipmap-*/ic_launcher_foreground.png` (흰 심볼, 투명) → `app/src/main/res/`로 복사
- 배경은 repo `colors.xml`의 `ic_launcher_background = #0D1B3E` 그대로 (네이비)
- repo의 placeholder `drawable/ic_launcher_foreground.xml` 제거 후
  `mipmap-anydpi-v26/ic_launcher.xml`의 `foreground`/`monochrome` → `@mipmap/ic_launcher_foreground`
- **권장**: Android Studio → Image Asset → Foreground=`in-app/pigos-symbol-white.svg`, Background=#0D1B3E

### Legacy — `android/legacy-mipmap/`
- 밀도별 `ic_launcher.png`(네이비 라운드) + `ic_launcher_round.png`(원형) → `app/src/main/res/`로 복사 (API24/25 폴백)

## 인앱 로고 원본 — `in-app/`
- `pigos-horizontal-light.png` / `-dark.png` (+`-tagline` 버전)
- `pigos-symbol-color.svg` / `pigos-symbol-white.svg` (권위 벡터)

> ⚠️ 정적 생성물. Android는 머지 전 Android Studio 빌드 + 런처 미리보기 확인 필수.
