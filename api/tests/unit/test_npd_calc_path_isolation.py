"""NPD/WEI 계산 경로는 v_sow_npd 를 쓰지 않는다 — 재시도 금지 가드.

## 배경: 한 번 시도했다가 되돌렸다 (2026-08-25)

`v_sow_npd` 는 내부에서 `CURRENT_DATE` 로 유휴 cap 을 판정한다. 그래서 계산 경로는
`:as_of` 를 명시적으로 바인드하는 repository 쿼리로 옮겨져 있다(f7a1c3e5b9d0).

2026-08-25 대시보드 지연 대응 중 "as_of == 오늘이면 뷰와 결과가 같으니 핫패스만 뷰로"
라는 최적화를 넣었다가 **되돌렸다.** 되돌린 이유 두 가지를 여기 고정한다 —
같은 아이디어가 다시 나올 만큼 그럴듯하기 때문이다.

### ① 이득이 없었다

느렸던 건 `_NPD_SQL` 의 `lact_open` LATERAL 이었고, `farrowings(sow_id, farrowing_date)`
인덱스(e2b5d7c9a1f3)로 해결됐다. 그 뒤 프로덕션 실측(141,359두 / 66농장):

    1만두 농장   인라인 0.030s  /  뷰 0.029s   (값 동일)
    중앙값 농장  인라인 0.011s  /  뷰 0.011s

### ② 틀릴 수 있었다 — 테스트로는 못 잡히는 방식으로

등가성의 전제는 "뷰의 `CURRENT_DATE` == `as_of`" 인데, 실제 운영은:

    API 컨테이너 TZ = UTC
    DB TZ          = Asia/Seoul

★ 매일 **00:00~09:00 KST 의 9시간** 동안 DB 날짜가 컨테이너보다 하루 앞선다.
  그 창에서 뷰의 cap 조건은 `weaning_date <= as_of - 59` 가 되어 인라인
  (`<= as_of - 60`)보다 하루 느슨해진다 → 이유 후 59일 된 모돈이 하루 일찍
  cap 60 으로 잡혀 평균 WEI 가 달라진다.

  **테스트 환경은 컨테이너와 DB 의 TZ 가 같아 이 결함을 재현하지 못한다.**
  즉 "테스트가 통과했으니 등가"라는 근거가 성립하지 않는 종류의 결함이었다.

그래서 이 파일은 값을 비교하지 않는다 — **계산 SQL 이 뷰를 참조하지 않는다는 사실
자체**를 잠근다. 값 비교로는 못 잡는 것을 구조로 잡는다.
"""
import inspect
import re

from app.repositories import npd_repo

# 계산 경로에 있어서는 안 되는 것들.
FORBIDDEN = {
    "v_sow_npd": "뷰는 CURRENT_DATE 로 cap 을 판정한다 — as_of 계약이 깨진다",
    "v_farm_psy": "같은 이유(뷰 내부 CURRENT_DATE)",
    "CURRENT_DATE": "기준일은 :as_of 여야 한다",
    "now()": "기준일은 :as_of 여야 한다",
}


def _sql_strings() -> dict[str, str]:
    """모듈이 들고 있는 SQL 텍스트 전부 — 상수와 함수 본문 양쪽."""
    out: dict[str, str] = {}
    for name, obj in vars(npd_repo).items():
        if name.startswith("__"):
            continue
        text_attr = getattr(obj, "text", None)
        if isinstance(text_attr, str):
            out[name] = text_attr
        elif isinstance(obj, str) and "SELECT" in obj.upper():
            out[name] = obj
    return out


def test_no_view_or_wallclock_in_module_sql():
    """★ 모듈의 모든 SQL 상수가 뷰·벽시계를 참조하지 않는다."""
    for name, sql in _sql_strings().items():
        stripped = re.sub(r"--.*", "", sql)      # SQL 라인 주석 제거
        for token, why in FORBIDDEN.items():
            assert token.lower() not in stripped.lower(), (
                f"{name} 에 `{token}` 이 있다 — {why}.\n"
                "이 파일 머리말의 '되돌린 이유 ②'를 먼저 읽으십시오."
            )


def test_public_functions_use_exactly_one_sql_path():
    """★ as_of 값에 따라 다른 SQL 을 고르는 분기가 없어야 한다.

    되돌린 최적화가 정확히 `stmt = _AVG_VIEW if as_of == date.today() else _AVG` 였다.
    분기 자체가 "어떤 조건에서는 다른 정의로 계산한다"는 뜻이라 결정론이 깨진다.

    문자열로 `if` 를 찾으면 삼항 연산자(`float(x) if x else None`)에 걸리므로,
    **함수가 참조하는 모듈 SQL 상수의 개수**로 판정한다."""
    sql_names = set(_sql_strings())
    for fn in (npd_repo.avg_wei_days, npd_repo.sum_wei_days):
        src = inspect.getsource(fn)
        assert "date.today()" not in src, (
            f"{fn.__name__} 이 벽시계를 본다 — 기준일은 호출자가 준 as_of 뿐이어야 한다")
        used = {n for n in sql_names if re.search(rf"\b{re.escape(n)}\b", src)}
        assert len(used) == 1, (
            f"{fn.__name__} 이 SQL 상수를 {len(used)}개 참조한다({sorted(used)}) — "
            "경로가 하나여야 결정론이 유지된다. 이 파일 머리말을 먼저 읽으십시오.")


def test_as_of_is_bound_in_every_calculation_query():
    """계산 SQL 은 :as_of 를 실제로 바인드해야 한다 — 안 쓰면 기준일이 없는 것과 같다."""
    for name, sql in _sql_strings().items():
        if "wei_days" not in sql:
            continue
        assert ":as_of" in sql, f"{name} 이 :as_of 를 바인드하지 않는다"


def test_forbidden_list_is_not_silently_emptied():
    """가드 목록이 비면 이 파일 전체가 무력해진다 — 그 자체를 잠근다."""
    assert "v_sow_npd" in FORBIDDEN and "CURRENT_DATE" in FORBIDDEN
