import { cookies } from "next/headers";
import { getRequestConfig } from "next-intl/server";
import { defaultLocale, locales, type Locale } from "./config";

// 로케일 단일 소스 = NEXT_LOCALE 쿠키 (언어 토글이 쿠키 set + router.refresh).
// 쿠키 없으면 defaultLocale. → 사이드바(chrome)와 페이지(next-intl)가 같은 언어 사용.
export default getRequestConfig(async () => {
  const cookieLocale = (await cookies()).get("NEXT_LOCALE")?.value;
  const locale: string =
    cookieLocale && locales.includes(cookieLocale as Locale) ? cookieLocale : defaultLocale;

  return {
    locale,
    messages: (await import(`../messages/${locale}.json`)).default,
  };
});
