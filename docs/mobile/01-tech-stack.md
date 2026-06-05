# Android 기술 스택

## 결정 배경

현장 작업자 + Android 우선 + 오프라인 입력 + 저사양 기기 + 백그라운드 동기화 조합.
React Native 대신 Kotlin Native 선택 — 오프라인 퍼스트 구조, 디바이스 제어, 저사양 성능 튜닝에서 우위.

---

## 기술 스택

| 영역 | 기술 | 비고 |
|------|------|------|
| 언어 | Kotlin | |
| UI | Jetpack Compose | Material 3 |
| 아키텍처 | MVVM + Clean Architecture | UI → ViewModel → UseCase → Repository |
| DI | Hilt | |
| 네트워크 | Retrofit 2 + OkHttp 3 | Gson/Moshi 직렬화 |
| 로컬 DB | Room | 오프라인 저장소 |
| 백그라운드 동기화 | WorkManager | 배터리 최적화 자동 적용 |
| 설정/토큰 저장 | DataStore (Preferences) | accessToken, refreshToken, activeFarmId |
| 비동기 | Kotlin Coroutines + Flow | |
| 네비게이션 | Navigation Compose | |
| 이미지 | Coil | |
| 날짜 | java.time (API 26+) | minSdk 26 권장 |

---

## build.gradle 핵심 의존성

```kotlin
// Compose
implementation("androidx.compose.ui:ui")
implementation("androidx.compose.material3:material3")
implementation("androidx.activity:activity-compose:1.9.0")
implementation("androidx.navigation:navigation-compose:2.7.7")

// Lifecycle / ViewModel
implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.0")
implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.0")

// Hilt
implementation("com.google.dagger:hilt-android:2.51")
kapt("com.google.dagger:hilt-compiler:2.51")
implementation("androidx.hilt:hilt-navigation-compose:1.2.0")

// Retrofit
implementation("com.squareup.retrofit2:retrofit:2.11.0")
implementation("com.squareup.retrofit2:converter-gson:2.11.0")
implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")

// Room
implementation("androidx.room:room-runtime:2.6.1")
implementation("androidx.room:room-ktx:2.6.1")
kapt("androidx.room:room-compiler:2.6.1")

// WorkManager
implementation("androidx.work:work-runtime-ktx:2.9.0")
implementation("androidx.hilt:hilt-work:1.2.0")

// DataStore
implementation("androidx.datastore:datastore-preferences:1.1.1")

// Coil
implementation("io.coil-kt:coil-compose:2.6.0")
```

---

## 아키텍처 레이어

```
app/
├── ui/
│   ├── screens/          ← Composable 화면 (Dashboard, Sows, Chat...)
│   ├── components/       ← 공용 UI 컴포넌트
│   └── theme/            ← Color, Typography, Shape
├── viewmodel/            ← ViewModel (화면당 1개)
├── domain/
│   ├── usecase/          ← 비즈니스 로직 단위
│   └── model/            ← 도메인 모델 (DTO와 분리)
├── data/
│   ├── remote/
│   │   ├── api/          ← Retrofit 인터페이스
│   │   └── dto/          ← 서버 응답 데이터 클래스
│   ├── local/
│   │   ├── dao/          ← Room DAO
│   │   └── entity/       ← Room Entity
│   └── repository/       ← Remote + Local 통합
└── di/                   ← Hilt 모듈
```

---

## minSdk / targetSdk

```kotlin
minSdk = 26          // Android 8.0 — 동남아/중국 저가 기기 커버
targetSdk = 34       // Android 14
compileSdk = 34
```

---

## 권한 (AndroidManifest.xml)

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
<uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" />  <!-- 재부팅 후 WorkManager 재스케줄 -->
<uses-permission android:name="android.permission.POST_NOTIFICATIONS" />      <!-- Android 13+ 알림 -->
<uses-permission android:name="android.permission.CAMERA" />                   <!-- 귀표 사진, 향후 -->
```
