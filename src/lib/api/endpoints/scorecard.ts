import { apiClient } from "@/lib/api/client";
import type { ScorecardRequest, ScorecardResponse } from "@/types/api.types";

// 무가입 공개 엔드포인트 — 인증 불필요.
export const scorecardApi = {
  compute: (body: ScorecardRequest) =>
    apiClient.post<ScorecardResponse>("/api/v1/scorecard", body).then((r) => r.data),
};
