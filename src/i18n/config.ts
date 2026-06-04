export const locales = ["en", "ko", "zh", "es", "vi"] as const;
export type Locale = (typeof locales)[number];
export const defaultLocale: Locale = "en";
