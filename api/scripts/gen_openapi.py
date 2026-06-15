"""
OpenAPI 스펙 생성기 — 라이브 FastAPI 앱에서 docs/api/openapi-v1.yaml 생성.

수기 관리가 드리프트하는 문제 해결: 라우트 변경 후 이 스크립트로 재생성하면
스펙이 항상 실제 라우트와 100% 일치한다. (모바일 계약서가 참조)

실행: cd api && uv run python scripts/gen_openapi.py
"""
import sys
from pathlib import Path

import yaml

# scripts/ 에서 실행 시 api/ 를 import 경로에 추가
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app  # noqa: E402

# FastAPI가 생성한 OpenAPI (paths는 /api/v1/... 풀패스 포함)
spec = app.openapi()

# 서버/연락처/설명 보강 (paths가 /api/v1 포함하므로 server는 호스트 루트)
spec["servers"] = [
    {"url": "https://api.pigos.io", "description": "Production"},
    {"url": "http://localhost:8000", "description": "Local dev (iOS 시뮬)"},
    {"url": "http://10.0.2.2:8000", "description": "Local dev (Android 에뮬)"},
]
spec.setdefault("info", {})
spec["info"]["description"] = (
    "Global Swine Farm Management SaaS — Base API + AI Addon platform.\n\n"
    "이 파일은 라이브 라우트에서 자동 생성됨 (scripts/gen_openapi.py). 수기 편집 금지.\n"
    "사람용 연동 계약서: docs/mobile-integration-contract.md\n\n"
    "인증: Bearer JWT (/api/v1/auth/login). access 15분 / refresh 7일.\n"
    "멀티테넌트: 모든 농장 데이터는 farm_id로 격리."
)
spec["info"]["contact"] = {"name": "PigOS Support", "url": "https://pigos.io"}
spec["info"]["license"] = {"name": "Proprietary"}

out = Path(__file__).resolve().parents[2] / "docs" / "api" / "openapi-v1.yaml"
header = "# AUTO-GENERATED — do not edit by hand. Regenerate: cd api && uv run python scripts/gen_openapi.py\n"
out.write_text(header + yaml.safe_dump(spec, allow_unicode=True, sort_keys=False), encoding="utf-8")
print(f"wrote {out}  ({len(spec['paths'])} paths, {len(spec.get('components', {}).get('schemas', {}))} schemas)")
