# PigOS — 검수/리팩토링 지침

> 퇴근 후 자율 실행 모드 (review mode)
> `claude --dangerously-skip-permissions -p "CLAUDE_REVIEW.md의 검수 지침을 따라 진행"` 으로 실행

---

## 검수 실행 원칙

1. **먼저 오늘 구현된 것을 파악한다**
   ```bash
   git log --oneline --since="today 00:00"
   git diff HEAD~<오늘 커밋 수>..HEAD --stat
   ```

2. **아래 검수 항목 순서대로 진행**한다

3. 개선사항 발견 시 즉시 수정 → `git commit` (`refactor:` 또는 `fix:` prefix)

4. 검수 완료 후 `REVIEW.md`에 결과 기록

5. **git push 금지** — 내일 사람이 직접 확인 후 push

---

## 검수 항목 (우선순위 순)

### 1. 타입 안전성
- [ ] Python type hint 누락 함수/변수 확인 (`mypy` 또는 `pyright` 기준)
- [ ] Optional/None 처리 누락 부분
- [ ] Pydantic 스키마와 실제 DB 컬럼 타입 불일치

### 2. 코드 중복/구조
- [ ] 3회 이상 반복되는 로직 → 공통 함수/클래스로 추출
- [ ] CRUD 패턴이 모듈마다 다르게 구현된 부분 → 통일
- [ ] 불필요한 주석, TODO 중 이미 완료된 것 정리

### 3. 보안
- [ ] SQL Injection 위험 부분 (raw query 사용 시)
- [ ] 인증/인가 체크 누락된 엔드포인트
- [ ] 민감 정보 (비밀번호, 토큰) 로그 출력 여부

### 4. 성능
- [ ] N+1 쿼리 패턴 → `joinedload` / `selectinload` 적용
- [ ] 인덱스 없는 필터 컬럼 (farm_id, period 등 자주 쓰는 것)
- [ ] 대용량 쿼리에 페이지네이션 누락

### 5. 테스트
- [ ] 핵심 비즈니스 로직 (KPI 계산, 월마감) 테스트 없으면 추가
- [ ] Happy path만 있고 에러 케이스 없는 테스트 보완

### 6. 문서
- [ ] 새로 추가된 API 엔드포인트 OpenAPI 주석 확인
- [ ] `PROGRESS.md` 내용 보고 내일 구현 우선순위 제안 추가

---

## 금지 사항

- `git push` 금지
- 실제 DB (Oracle PKSU) 데이터 변경 금지
- AWS 리소스 변경 금지
- 기능 추가 금지 — 검수/개선만 (새 기능은 내일 구현 모드에서)

---

## 검수 완료 후 REVIEW.md 작성 양식

```markdown
## YYYY-MM-DD 검수 결과

### 검수한 커밋
- <commit hash> <메시지>
- ...

### 개선한 내용
- ...

### 잔여 이슈 (다음에 처리)
- ...

### 내일 구현 제안
- ...
```
