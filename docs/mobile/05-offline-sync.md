# 오프라인 동기화 (Android)

서버 스펙: `docs/specs/2026-05-19_offline-sync-spec.md`

---

## 원칙

1. **오프라인 우선** — 네트워크 없어도 기록 가능. Room에 먼저 저장
2. **Last-Write-Wins** — 충돌 시 최신 타임스탬프 우선
3. **멱등성** — 같은 요청 여러 번 보내도 결과 동일
4. **백그라운드 자동 동기화** — WorkManager가 처리, 배터리 최적화 자동 적용

---

## Room 로컬 DB 구조

```kotlin
@Database(
    entities = [
        SowEntity::class,
        MatingEntity::class,
        FarrowingEntity::class,
        WeaningEntity::class,
        SyncQueueEntity::class,
    ],
    version = 1
)
abstract class PigOsDatabase : RoomDatabase() {
    abstract fun sowDao(): SowDao
    abstract fun matingDao(): MatingDao
    abstract fun farrowingDao(): FarrowingDao
    abstract fun weaningDao(): WeaningDao
    abstract fun syncQueueDao(): SyncQueueDao
}
```

---

## SyncQueue (동기화 대기열)

오프라인에서 생성/수정된 레코드를 대기열에 쌓고, 연결 시 서버로 전송합니다.

```kotlin
@Entity(tableName = "sync_queue")
data class SyncQueueEntity(
    @PrimaryKey val id: String = UUID.randomUUID().toString(),
    val entityType: String,    // "mating" | "farrowing" | "weaning" | "sow" ...
    val entityId: String,
    val operation: String,     // "CREATE" | "UPDATE" | "DELETE"
    val payload: String,       // JSON
    val offlineCreatedAt: Long = System.currentTimeMillis(),
    val synced: Boolean = false,
    val retryCount: Int = 0
)
```

---

## 기록 흐름

```
사용자 입력 (예: 교배 기록)
    ↓
1. Room 저장 (MatingEntity) — 즉시
2. SyncQueue에 추가 (operation = "CREATE")
3. UI 업데이트 (낙관적 업데이트)
    ↓
네트워크 연결 감지 (ConnectivityManager)
    ↓
WorkManager SyncWorker 실행
    ↓
POST /farms/{farm_id}/sync
    ↓
성공 → SyncQueue 항목 synced = true
실패 → retryCount 증가, WorkManager 재스케줄
```

---

## SyncWorker 구현

```kotlin
@HiltWorker
class SyncWorker @AssistedInject constructor(
    @Assisted appContext: Context,
    @Assisted params: WorkerParameters,
    private val syncRepository: SyncRepository
) : CoroutineWorker(appContext, params) {

    override suspend fun doWork(): Result {
        val farmId = inputData.getString("farm_id") ?: return Result.failure()

        return try {
            val pendingItems = syncRepository.getPendingSyncItems()
            if (pendingItems.isEmpty()) return Result.success()

            syncRepository.syncToServer(farmId, pendingItems)
            Result.success()
        } catch (e: Exception) {
            if (runAttemptCount < 3) Result.retry()
            else Result.failure()
        }
    }

    companion object {
        fun buildRequest(farmId: String): OneTimeWorkRequest {
            return OneTimeWorkRequestBuilder<SyncWorker>()
                .setInputData(workDataOf("farm_id" to farmId))
                .setConstraints(
                    Constraints.Builder()
                        .setRequiredNetworkType(NetworkType.CONNECTED)
                        .build()
                )
                .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.SECONDS)
                .build()
        }
    }
}
```

---

## Sync API 요청/응답

```
POST /api/v1/farms/{farm_id}/sync

Request:
{
  "client_id": "device-uuid",
  "last_sync_at": "2026-06-04T10:00:00Z",  // null이면 전체 다운로드
  "changes": [
    {
      "entity": "matings",
      "operation": "CREATE",
      "id": "local-uuid",
      "payload": { ... },
      "offline_created_at": "2026-06-05T06:30:00Z"
    }
  ]
}

Response:
{
  "accepted": ["local-uuid-1", "local-uuid-2"],
  "rejected": [],
  "server_changes": [
    {
      "entity": "sows",
      "operation": "UPDATE",
      "id": "server-uuid",
      "payload": { ... }
    }
  ],
  "sync_token": "2026-06-05T09:00:00Z"
}
```

---

## 네트워크 상태 감지

```kotlin
// 연결 복구 시 자동 동기화 트리거
class NetworkObserver @Inject constructor(
    private val context: Context
) {
    fun observe(): Flow<Boolean> = callbackFlow {
        val manager = context.getSystemService(ConnectivityManager::class.java)
        val callback = object : ConnectivityManager.NetworkCallback() {
            override fun onAvailable(network: Network) { trySend(true) }
            override fun onLost(network: Network) { trySend(false) }
        }
        manager.registerDefaultNetworkCallback(callback)
        awaitClose { manager.unregisterNetworkCallback(callback) }
    }
}
```

---

## 오프라인 상태 UI

- 화면 상단 배너: "오프라인 — 데이터는 로컬에 저장됩니다"
- 동기화 중 표시: 아이콘 + "동기화 중..."
- 마지막 동기화 시간 표시
- 미전송 기록 개수 뱃지
