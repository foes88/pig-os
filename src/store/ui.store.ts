import { create } from "zustand";

interface UiState {
  upgradeModalOpen: boolean;
  upgradeModalFeature: string | null;
  sidebarOpen: boolean;
  locale: "en" | "ko" | "es" | "zh";

  openUpgradeModal: (feature?: string) => void;
  closeUpgradeModal: () => void;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;
  setLocale: (locale: "en" | "ko" | "es" | "zh") => void;
}

export const useUiStore = create<UiState>()((set) => ({
  upgradeModalOpen: false,
  upgradeModalFeature: null,
  sidebarOpen: true,
  locale: "en",

  openUpgradeModal: (feature) =>
    set({ upgradeModalOpen: true, upgradeModalFeature: feature ?? null }),
  closeUpgradeModal: () =>
    set({ upgradeModalOpen: false, upgradeModalFeature: null }),

  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),

  setLocale: (locale) => set({ locale }),
}));
