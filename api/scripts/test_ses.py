"""SES/이메일 발송 준비 점검 — 한 번 실행해 실제 발송을 확인.

사용:
  cd api && uv run python scripts/test_ses.py you@example.com

동작:
  - 현재 설정(SES_FROM_EMAIL 있으면 SES, 없으면 SMTP, 둘 다 없으면 로그 폴백)으로 테스트 메일 1통 발송.
  - 어떤 채널이 쓰였는지/성공 여부를 출력. 비밀값은 출력하지 않음.

env(배포 시크릿으로 주입, 코드/저장소에 커밋 금지):
  AWS_REGION=ap-northeast-2
  SES_FROM_EMAIL=hello@pigsignal.io   # 현재 인증된 발신주소(즉시 사용 가능). pigos.io 도메인 인증 후 교체 권장.
  APP_BASE_URL=https://app.pigos.io
  AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY  # 또는 EC2/ECS IAM 롤(권장)
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # api/ 를 경로에 (직접 실행 지원)

from app.core.config import settings  # noqa: E402
from app.services.email_service import send_email  # noqa: E402


async def main() -> int:
    to = sys.argv[1] if len(sys.argv) > 1 else ""
    if not to:
        print("사용법: uv run python scripts/test_ses.py <받는사람@메일>")
        return 2

    provider = "SES" if settings.ses_configured else ("SMTP" if settings.smtp_configured else "없음(로그 폴백)")
    print(f"발송 채널: {provider}")
    if settings.ses_configured:
        print(f"  region={settings.aws_region}  from={settings.ses_from_email}")
    print(f"  app_base_url={settings.app_base_url}")
    if provider == "없음(로그 폴백)":
        print("  ⚠ SES/SMTP 미설정 — 실제 발송 안 됨. env 설정 후 다시 실행하세요.")

    ok = await send_email(
        to=to,
        subject="PigOS SES 발송 테스트",
        text_body="이 메일이 보이면 PigOS 이메일 발송 경로가 정상입니다.",
        html_body="<p>이 메일이 보이면 <b>PigOS 이메일 발송 경로</b>가 정상입니다.</p>",
    )
    print(f"결과: {'✅ 발송 성공' if ok else '❌ 발송 안 됨(위 채널/자격증명/발신주소 인증 확인)'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
