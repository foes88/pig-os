import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { UserProfile } from "@/types/api.types";
import { resetAnalytics } from "@/lib/analytics";

interface AuthState {
  user: UserProfile | null;
  accessToken: string | null;
  refreshToken: string | null;
  activeFarmId: string | null;

  setAuth: (
    user: UserProfile,
    accessToken: string,
    refreshToken: string,
    farmId?: string
  ) => void;
  setAccessToken: (token: string) => void;
  setUser: (user: UserProfile) => void;
  setActiveFarmId: (farmId: string) => void;
  clearAuth: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      activeFarmId: null,

      setAuth: (user, accessToken, refreshToken, farmId) => {
        // stale activeFarmId 보정: 명시값 > 기존값(접근가능할 때) > 첫 농장.
        // 멤버십 회수/농장 삭제로 더는 접근 못 하는 농장을 가리키면 첫 농장으로 리셋.
        // farm_ids가 비면(super_admin 등 — /farms는 전체 반환) 기존 선택을 보존(스위처가 설정).
        const ids = user.farm_ids ?? [];
        const desired = farmId ?? get().activeFarmId;
        const active = ids.length === 0
          ? desired ?? null
          : desired && ids.includes(desired) ? desired : ids[0];
        set({ user, accessToken, refreshToken, activeFarmId: active });
      },

      setAccessToken: (token) => set({ accessToken: token }),

      // /me 재조회로 사용자(역할·farm_roles·접근농장) 최신화 + stale activeFarmId 보정.
      // farm_ids가 비면(super_admin 등 — /farms는 전체 반환) 기존 선택 보존(스위처가 설정).
      setUser: (user) => {
        const ids = user.farm_ids ?? [];
        const cur = get().activeFarmId;
        const active = ids.length === 0
          ? cur
          : cur && ids.includes(cur) ? cur : ids[0];
        set({ user, activeFarmId: active });
      },

      setActiveFarmId: (farmId) => set({ activeFarmId: farmId }),

      clearAuth: () => {
        resetAnalytics();
        set({ user: null, accessToken: null, refreshToken: null, activeFarmId: null });
      },

      isAuthenticated: () => {
        const { accessToken } = get();
        return !!accessToken;
      },
    }),
    {
      name: "pigos-auth",
      storage: createJSONStorage(() => localStorage),
      // Only persist identity — access token is short-lived but persisted for UX
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        activeFarmId: state.activeFarmId,
      }),
    }
  )
);
