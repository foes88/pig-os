#!/usr/bin/env bash
# PreToolUse(Bash) guard — CLAUDE.md 자율모드 금지사항 강제.
# jq 비의존(grep만). 차단 시 JSON permissionDecision:deny + exit 0 (exit 2 버그 회피).
input=$(cat)
cmd=$(printf '%s' "$input" | grep -oE '"command"[[:space:]]*:[[:space:]]*"([^"\\]|\\.)*"' | head -n1 | sed -E 's/^"command"[[:space:]]*:[[:space:]]*"//; s/"$//')
[ -z "$cmd" ] && exit 0

deny() {
  reason="$1"
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}\n' "$reason"
  exit 0
}

# 1) git push — 사용자가 명시적으로 요청 시 허용

# 2) Oracle/PKSU 실데이터 쓰기성 작업 금지
echo "$cmd" | grep -Eiq 'PKSU' && \
  echo "$cmd" | grep -Eiq '(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|MERGE|GRANT)' && \
  deny "BLOCKED: Oracle PKSU 원본은 읽기 전용. 쓰기/DDL 금지(CLAUDE.md). 읽기 쿼리만 사용하세요."
echo "$cmd" | grep -Eiq '(sqlplus|sqlcl|sql[[:space:]]).*PKSU' && \
  deny "BLOCKED: PKSU 실데이터 접속 차단(CLAUDE.md). 읽기 전용 경로만 사용하세요."

# 3) AWS 리소스 생성/변경 금지 (조회성 제외)
echo "$cmd" | grep -Eq '(^|[^a-zA-Z])aws[[:space:]]' && \
  echo "$cmd" | grep -Eiq '(create|delete|terminate|run-instances|put-|update-|modify-|deploy|destroy|remove-)' && \
  deny "BLOCKED: AWS 리소스 생성/변경 금지(CLAUDE.md). 조회(describe/list/get)만 허용."
echo "$cmd" | grep -Eiq '(terraform[[:space:]]+(apply|destroy)|cdk[[:space:]]+(deploy|destroy))' && \
  deny "BLOCKED: 인프라 apply/destroy 금지(CLAUDE.md). plan/diff까지만."

exit 0
