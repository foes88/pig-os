/**
 * P0-FE — 이벤트 입력 폼 Zod 스키마 (DEV_GUIDE §5-B).
 * 백엔드 validator(api/app/validators)와 동일 기준의 클라이언트 사전검증.
 * 모바일도 동일 API를 쓰므로 최종 권위는 백엔드 — 이건 즉시 UX 피드백용.
 *
 * 에러 메시지는 i18n 키(코드)만 담는다 → firstError(schema, data, tv)가 tv(code)로 번역.
 */
import { z } from "zod";

/** YYYY-MM-DD 문자열이 오늘(로컬) 이후가 아닌지. */
const notFuture = (d: string) => {
  const today = new Date();
  today.setHours(23, 59, 59, 999);
  return new Date(d) <= today;
};

const dateNotFuture = z.string().min(1, "dateRequired").refine(notFuture, "futureDate");

// ── FE-1 분만 ───────────────────────────────────────────────────────────────
export const farrowingSchema = z
  .object({
    farrowing_date: dateNotFuture,
    total_born: z.number().int().min(0).max(35, "totalBornMax"),
    born_alive: z.number().int().min(0).max(35),
    stillborn: z.number().int().min(0).max(25, "stillbornMax"),
    mummified: z.number().int().min(0).max(25, "mummifiedMax"),
    avg_birth_weight_kg: z.number().min(0).max(3.0, "birthWeightMax").optional(),
  })
  .refine((d) => d.total_born === d.born_alive + d.stillborn + d.mummified, {
    message: "bornAliveSum",
    path: ["total_born"],
  });

// ── FE-2 이유 ───────────────────────────────────────────────────────────────
export const weaningSchema = z.object({
  weaning_date: dateNotFuture,
  weaned_count: z.number().int().min(0, "weanCountMin"),
  avg_weaning_weight_kg: z.number().min(2.0, "weanWeightRange").max(12.0, "weanWeightRange").optional(),
});

// ── FE-3 교배 ───────────────────────────────────────────────────────────────
export const matingSchema = z.object({
  mating_date: dateNotFuture,
});

// ── FE-4 자돈 이벤트(폐사/양자) ───────────────────────────────────────────────
export const pigletEventSchema = z
  .object({
    event_type: z.enum(["FOSTER_IN", "FOSTER_OUT", "DEATH"]),
    event_date: dateNotFuture,
    piglet_count: z.number().int().min(1, "countMin1").max(30),
    target_sow_id: z.string().uuid().optional(),
  })
  .refine((d) => d.event_type === "DEATH" || !!d.target_sow_id, {
    message: "fosterTargetRequired",
    path: ["target_sow_id"],
  });

// ── FE-5 도폐사 ─────────────────────────────────────────────────────────────
export const cullSchema = z.object({
  removal_type: z.enum(["CULLED", "DEAD", "SOLD", "TRANSFER"]),
  removal_date: dateNotFuture,
  body_weight_kg: z.number().min(0).max(99999).optional(),
});

// ── FE-6 모돈 전입 ───────────────────────────────────────────────────────────
export const sowEntrySchema = z.object({
  ear_tag: z.string().min(1, "earTagRequired"),
  entry_date: dateNotFuture,
  entry_type: z.enum(["GILT", "PURCHASE", "TRANSFER", "BORN"]),
});

// ── FE-7 비육돈 입식/출하 ─────────────────────────────────────────────────────
export const finisherEntrySchema = z.object({
  group_code: z.string().min(1, "groupCodeRequired").max(30),
  start_date: dateNotFuture,
  head_count_in: z.number().int().min(1, "headCountMin"),
  avg_entry_weight_kg: z.number().min(5, "entryWeightRange").max(50, "entryWeightRange").optional(),
});

export const finisherShipSchema = z.object({
  end_date: dateNotFuture,
  head_count_out: z.number().int().min(1, "headCountMin"),
  avg_exit_weight_kg: z.number().min(0).max(200, "exitWeightMax").optional(),
});

/**
 * 스키마로 data를 검증하고, 실패 시 첫 이슈 메시지를 번역해 반환. 통과 시 null.
 * @param tv useTranslations("validation") 번역기
 */
export function firstError<T>(
  schema: z.ZodType<T>,
  data: unknown,
  tv: (key: string) => string,
): string | null {
  const r = schema.safeParse(data);
  if (r.success) return null;
  const code = r.error.issues[0]?.message ?? "invalid";
  // 코드가 등록된 i18n 키가 아니면(zod 기본 메시지) 일반 메시지로 폴백
  const known = /^[a-zA-Z]+$/.test(code) && code.length < 40;
  return known ? tv(code) : tv("invalid");
}
