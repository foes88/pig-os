# 인증 플로우 (JWT)

## 개요

PigOS API는 JWT 기반 인증을 사용합니다.
- **Access Token**: 15분 만료, API 호출에 사용
- **Refresh Token**: 7일 만료, Access Token 재발급에 사용
- 두 토큰 모두 **DataStore**에 저장

---

## 인증 흐름

```
앱 시작
  ↓
DataStore에 accessToken 있음?
  ├─ 없음 → LoginScreen
  └─ 있음 → API 호출
              ↓
           401 응답?
             ├─ 아니오 → 정상 처리
             └─ 예 → POST /api/v1/auth/refresh
                       ↓
                    성공? → 새 accessToken 저장 → 원래 요청 재시도
                    실패? → LoginScreen (토큰 만료)
```

---

## API 엔드포인트

### 로그인
```
POST /api/v1/auth/login

Request:
{
  "email": "farmer@example.com",
  "password": "password123"
}

Response:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "farmer@example.com",
    "name": "홍길동",
    "role": "OWNER",
    "farm_ids": ["uuid"]
  }
}
```

### 토큰 갱신
```
POST /api/v1/auth/refresh

Request:
{
  "refresh_token": "eyJ..."
}

Response:
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### 로그아웃
```
POST /api/v1/auth/logout
Authorization: Bearer {accessToken}
```

### 내 정보
```
GET /api/v1/auth/me
Authorization: Bearer {accessToken}

Response:
{
  "id": "uuid",
  "email": "farmer@example.com",
  "name": "홍길동",
  "role": "OWNER",
  "farm_ids": ["uuid"]
}
```

---

## OkHttp Interceptor 구현

```kotlin
class AuthInterceptor @Inject constructor(
    private val dataStore: DataStore<Preferences>
) : Interceptor {

    override fun intercept(chain: Interceptor.Chain): Response {
        val token = runBlocking {
            dataStore.data.map { it[PreferencesKeys.ACCESS_TOKEN] }.first()
        }

        val request = chain.request().newBuilder()
            .addHeader("Authorization", "Bearer $token")
            .build()

        val response = chain.proceed(request)

        // 401 → 토큰 갱신 후 재시도는 Authenticator에서 처리
        return response
    }
}

class TokenAuthenticator @Inject constructor(
    private val dataStore: DataStore<Preferences>,
    private val authApi: AuthApi
) : Authenticator {

    override fun authenticate(route: Route?, response: Response): Request? {
        val refreshToken = runBlocking {
            dataStore.data.map { it[PreferencesKeys.REFRESH_TOKEN] }.first()
        } ?: return null

        val newToken = runBlocking {
            authApi.refresh(RefreshRequest(refreshToken)).access_token
        }

        runBlocking {
            dataStore.edit { it[PreferencesKeys.ACCESS_TOKEN] = newToken }
        }

        return response.request.newBuilder()
            .header("Authorization", "Bearer $newToken")
            .build()
    }
}
```

---

## DataStore 키 정의

```kotlin
object PreferencesKeys {
    val ACCESS_TOKEN  = stringPreferencesKey("access_token")
    val REFRESH_TOKEN = stringPreferencesKey("refresh_token")
    val ACTIVE_FARM_ID = stringPreferencesKey("active_farm_id")
    val USER_ID       = stringPreferencesKey("user_id")
    val USER_NAME     = stringPreferencesKey("user_name")
    val USER_ROLE     = stringPreferencesKey("user_role")
}
```

---

## 멀티 농장

사용자는 여러 농장에 속할 수 있습니다.
- 로그인 시 `farm_ids` 배열로 모든 농장 ID 반환
- DataStore에 `activeFarmId` 저장
- 모든 API 호출에 `activeFarmId` 사용
- 농장 전환 시 `activeFarmId` 변경 (앱 재시작 불필요)
