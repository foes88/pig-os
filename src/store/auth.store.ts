import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { UserProfile } from "@/types/api.types";

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

      setAuth: (user, accessToken, refreshToken, farmId) =>
        set({
          user,
          accessToken,
          refreshToken,
          activeFarmId: farmId ?? user.farm_ids[0] ?? null,
        }),

      setAccessToken: (token) => set({ accessToken: token }),

      setActiveFarmId: (farmId) => set({ activeFarmId: farmId }),

      clearAuth: () =>
        set({ user: null, accessToken: null, refreshToken: null, activeFarmId: null }),

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
