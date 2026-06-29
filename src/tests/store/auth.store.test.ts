import { describe, it, expect, beforeEach } from "vitest";

import { useAuthStore } from "@/store/auth.store";
import type { UserProfile } from "@/types/api.types";

const user = (farm_ids: string[]): UserProfile => ({
  id: "u1", username: "u", email: "u@x.io", name: "U", role: "FARM_OWNER", farm_ids,
});

describe("auth.store setUser — activeFarmId 보정", () => {
  beforeEach(() => useAuthStore.getState().clearAuth());

  it("활성 농장 없으면 첫 농장으로 설정", () => {
    useAuthStore.getState().setUser(user(["f1", "f2"]));
    expect(useAuthStore.getState().activeFarmId).toBe("f1");
  });

  it("기존 활성 농장이 접근목록에 있으면 유지", () => {
    useAuthStore.getState().setUser(user(["f1", "f2"]));
    useAuthStore.getState().setActiveFarmId("f2");
    useAuthStore.getState().setUser(user(["f1", "f2", "f3"]));
    expect(useAuthStore.getState().activeFarmId).toBe("f2");
  });

  it("기존 활성 농장이 접근 불가가 되면 첫 농장으로 리셋(stale 보정)", () => {
    useAuthStore.getState().setUser(user(["f1", "f2"]));
    useAuthStore.getState().setActiveFarmId("f2");
    useAuthStore.getState().setUser(user(["f3", "f4"]));  // f2 회수됨
    expect(useAuthStore.getState().activeFarmId).toBe("f3");
  });

  it("접근 농장 0개면 null", () => {
    useAuthStore.getState().setUser(user([]));
    expect(useAuthStore.getState().activeFarmId).toBeNull();
  });
});
