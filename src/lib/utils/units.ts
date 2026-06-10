/**
 * Unit conversion and formatting utilities.
 * All values are stored as metric (kg, °C) in the DB.
 * Display conversion happens here based on FarmLocalConfig.weight_unit.
 */

export type WeightUnit = "kg" | "lb";

const KG_TO_LB = 2.20462;

export function kgToDisplay(kg: number | null | undefined, unit: WeightUnit): number | null {
  if (kg == null) return null;
  return unit === "lb" ? Math.round(kg * KG_TO_LB * 10) / 10 : kg;
}

export function lbToKg(lb: number): number {
  return Math.round((lb / KG_TO_LB) * 10) / 10;
}

export function formatWeight(
  kg: number | null | undefined,
  unit: WeightUnit,
  decimals = 1,
): string {
  const val = kgToDisplay(kg, unit);
  if (val == null) return "-";
  return `${val.toFixed(decimals)} ${unit}`;
}

export function formatCurrency(
  amount: number | null | undefined,
  symbol: string,
  decimals = 0,
): string {
  if (amount == null) return "-";
  const formatted = amount.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
  return `${symbol}${formatted}`;
}

/** Convert °C to °F for US/NA market display */
export function celsiusToDisplay(
  celsius: number | null | undefined,
  market: string | null | undefined,
): string {
  if (celsius == null) return "-";
  if (market === "NA") {
    return `${((celsius * 9) / 5 + 32).toFixed(1)}°F`;
  }
  return `${celsius.toFixed(1)}°C`;
}
