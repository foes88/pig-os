# 디자인 토큰 (Android)

웹(`src/app/globals.css`)의 CSS 변수를 Android Compose 테마로 변환합니다.

---

## Color (Compose)

```kotlin
// ui/theme/Color.kt

// Brand
val Navy         = Color(0xFF0D1B3E)
val Primary      = Color(0xFF2563EB)
val PrimaryDark  = Color(0xFF1D4ED8)
val PrimarySoft  = Color(0xFFEFF6FF)

// Surfaces (Light)
val Background   = Color(0xFFFAFAF9)
val Background2  = Color(0xFFF1F5F3)
val Surface      = Color(0xFFFFFFFF)
val PanelHi      = Color(0xFFF8F8F6)

// Text (Light)
val TextPrimary  = Color(0xFF0F172A)
val TextSecondary= Color(0xFF1E293B)
val TextMuted    = Color(0xFF64748B)
val TextFaint    = Color(0xFF94A3B8)

// Borders
val Border       = Color(0xFFE7E5E4)
val BorderStrong = Color(0xFFCBD5CF)

// Semantic
val Success      = Color(0xFF059669)
val Danger       = Color(0xFFDC2626)
val Warning      = Color(0xFFD97706)
val Purple       = Color(0xFF7C3AED)

// Surfaces (Dark)
val BackgroundDark  = Color(0xFF0A0F1E)
val Background2Dark = Color(0xFF0E1426)
val SurfaceDark     = Color(0xFF111933)
```

---

## Typography

```kotlin
// ui/theme/Type.kt

val PigOsTypography = Typography(
    // 페이지 제목
    headlineLarge = TextStyle(
        fontFamily = FontFamily.Default,
        fontWeight = FontWeight.ExtraBold,
        fontSize = 22.sp,
        letterSpacing = (-0.5).sp
    ),
    // 섹션 제목
    headlineMedium = TextStyle(
        fontWeight = FontWeight.Bold,
        fontSize = 18.sp
    ),
    // 카드 레이블
    titleMedium = TextStyle(
        fontWeight = FontWeight.SemiBold,
        fontSize = 14.sp
    ),
    // 본문
    bodyMedium = TextStyle(
        fontWeight = FontWeight.Normal,
        fontSize = 14.sp
    ),
    // 보조 텍스트
    bodySmall = TextStyle(
        fontWeight = FontWeight.Normal,
        fontSize = 12.sp,
        color = TextMuted
    ),
    // 캡션
    labelSmall = TextStyle(
        fontWeight = FontWeight.Medium,
        fontSize = 10.sp,
        letterSpacing = 0.5.sp
    )
)

// KPI 숫자 — Monospace
val MonoStyle = TextStyle(
    fontFamily = FontFamily.Monospace,
    fontWeight = FontWeight.ExtraBold,
    fontSize = 28.sp
)
```

---

## Shape (둥근 모서리)

```kotlin
// ui/theme/Shape.kt
val PigOsShapes = Shapes(
    small  = RoundedCornerShape(8.dp),   // 버튼
    medium = RoundedCornerShape(12.dp),  // 입력 필드
    large  = RoundedCornerShape(14.dp),  // 카드
)
```

---

## 간격 (Spacing)

```kotlin
object Spacing {
    val xs  = 4.dp
    val sm  = 8.dp
    val md  = 16.dp
    val lg  = 24.dp
    val xl  = 32.dp
    val xxl = 48.dp

    // 페이지 좌우 패딩
    val pagePadding = 16.dp
    // 카드 내부 패딩
    val cardPadding = 16.dp
}
```

---

## 상태 색상 매핑

| 상태 | 배경 | 텍스트 | 용도 |
|------|------|--------|------|
| OK / 정상 | `#ECFDF5` | `#059669` | 정상 KPI, 완료 |
| WARNING | `#FFFBEB` | `#D97706` | 주의 필요 |
| CRITICAL | `#FEF2F2` | `#DC2626` | 즉시 조치 |
| INFO | `#EFF6FF` | `#2563EB` | 일반 정보 |

---

## 컴포넌트 스타일 가이드

### 기본 버튼
```kotlin
Button(
    colors = ButtonDefaults.buttonColors(containerColor = Primary),
    shape = RoundedCornerShape(8.dp)
) { Text("파일럿 신청") }
```

### 카드
```kotlin
Card(
    shape = RoundedCornerShape(14.dp),
    colors = CardDefaults.cardColors(containerColor = Surface),
    elevation = CardDefaults.cardElevation(defaultElevation = 1.dp)
) { ... }
```

### 상태 뱃지
```kotlin
Surface(
    color = when(severity) {
        "CRITICAL" -> Color(0xFFFEF2F2)
        "WARNING"  -> Color(0xFFFFFBEB)
        else       -> Color(0xFFECFDF5)
    },
    shape = RoundedCornerShape(50)
) { ... }
```
