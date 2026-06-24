import { cookies, headers } from "next/headers";
import { getRequestConfig } from "next-intl/server";
import { ADMIN_ONLY_LOCALES, defaultLocale, locales, type Locale } from "./config";

// 로케일 단일 소스 = NEXT_LOCALE 쿠키 (언어 토글이 쿠키 set + router.refresh).
// 쿠키 없으면 defaultLocale. → 사이드바(chrome)와 페이지(next-intl)가 같은 언어 사용.
// ⚠️ 한국어(ko)는 관리자 전용 → admin 호스트(admin.pigos.io)에서만 SSR 허용.
//    그 외(고객앱·로그인·localhost)에서 ko 쿠키가 남아있어도 defaultLocale로 강등(SSR 누수 차단).
export default getRequestConfig(async () => {
  const cookieLocale = (await cookies()).get("NEXT_LOCALE")?.value;
  const host = (await headers()).get("host") ?? "";
  const isAdminHost = host.startsWith("admin.");

  let locale: string = defaultLocale;
  if (cookieLocale && locales.includes(cookieLocale as Locale)) {
    const adminOnly = ADMIN_ONLY_LOCALES.includes(cookieLocale as Locale);
    locale = adminOnly && !isAdminHost ? defaultLocale : cookieLocale;
  }

  return {
    locale,
    messages: (await import(`../messages/${locale}.json`)).default,
  };
});
