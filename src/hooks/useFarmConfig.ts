"use client";

import { useQuery } from "@tanstack/react-query";
import { farmsApi } from "@/lib/api/endpoints/farms";
import { queryKeys } from "@/lib/api/queryKeys";
import { useAuthStore } from "@/store/auth.store";
import type { FarmLocalConfig } from "@/types/api.types";
import { formatWeight, formatCurrency, celsiusToDisplay } from "@/lib/utils/units";

const FALLBACK: FarmLocalConfig = {
  weight_unit: "kg",
  currency_code: "USD",
  currency_symbol: "$",
  min_wean_period: null,
  requires_traceability: false,
  requires_antibiotic_tracking: false,
  slaughter_weight_target_kg: null,
  market_code: null,
};

export function useFarmConfig() {
  const farmId = useAuthStore((s) => s.activeFarmId);

  const { data: config = FALLBACK } = useQuery({
    queryKey: queryKeys.farms.localConfig(farmId ?? ""),
    queryFn: () => farmsApi.getLocalConfig(farmId!),
    enabled: !!farmId,
    staleTime: 1000 * 60 * 10, // 10 min — rarely changes
  });

  return {
    config,
    /** Format a weight stored in kg to display string (e.g. "110 kg" or "243 lb") */
    fmtWeight: (kg: number | null | undefined, decimals = 1) =>
      formatWeight(kg, config.weight_unit, decimals),
    /** Format a currency amount */
    fmtCurrency: (amount: number | null | undefined, decimals = 0) =>
      formatCurrency(amount, config.currency_symbol, decimals),
    /** Format temperature — °C stored, converted to °F for NA market */
    fmtTemp: (celsius: number | null | undefined) =>
      celsiusToDisplay(celsius, config.market_code),
    weightUnit: config.weight_unit,
    currencySymbol: config.currency_symbol,
  };
}
