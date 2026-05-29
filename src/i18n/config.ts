export const locales = ["en", "ko", "es", "zh"] as const;
export type Locale = (typeof locales)[number];
export const defaultLocale: Locale = "en";
