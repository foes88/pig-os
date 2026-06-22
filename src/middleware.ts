import { NextRequest, NextResponse } from "next/server";

const PUBLIC_PATHS = ["/login", "/register", "/onboarding", "/forgot-password"];
const LOCALES = ["en", "ko", "zh", "es", "vi"];

// 첫 방문(쿠키 없음) 시 브라우저 언어(Accept-Language)로 자동 선택.
// 한국 브라우저→ko, 중국→zh, 스페인어권→es, 베트남→vi, 그 외→en. (GeoIP보다 정확·안전)
function detectLocale(req: NextRequest): string {
  const al = req.headers.get("accept-language") ?? "";
  for (const part of al.split(",")) {
    const base = part.trim().split(";")[0].split("-")[0].toLowerCase();
    if (LOCALES.includes(base)) return base;
  }
  return "en";
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow static assets and API routes through
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.includes(".")
  ) {
    return NextResponse.next();
  }

  // 자동 언어: NEXT_LOCALE 쿠키 없으면 브라우저 언어로 set (이후 사용자 토글이 덮어씀)
  const autoLocale = request.cookies.has("NEXT_LOCALE") ? null : detectLocale(request);
  const withLocale = (res: NextResponse) => {
    if (autoLocale) {
      res.cookies.set("NEXT_LOCALE", autoLocale, { path: "/", maxAge: 31536000, sameSite: "lax" });
    }
    return res;
  };

  const isPublic = PUBLIC_PATHS.some((p) => pathname.startsWith(p));
  // Auth token stored in localStorage — not accessible in middleware.
  // We use a lightweight session cookie set at login time for route protection.
  const hasSession = request.cookies.has("pigos_session");

  if (!isPublic && !hasSession) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", pathname);
    return withLocale(NextResponse.redirect(loginUrl));
  }

  if (isPublic && hasSession && pathname === "/login") {
    return withLocale(NextResponse.redirect(new URL("/", request.url)));
  }

  return withLocale(NextResponse.next());
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
