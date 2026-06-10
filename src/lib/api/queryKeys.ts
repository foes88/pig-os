// TanStack Query key factories — type-safe, co-located

export const queryKeys = {
  auth: {
    profile: () => ["auth", "profile"] as const,
  },

  farms: {
    all: () => ["farms"] as const,
    detail: (farmId: string) => ["farms", farmId] as const,
    localConfig: (farmId: string) => ["farms", farmId, "config"] as const,
    eventDefinitions: (farmId: string) => ["farms", farmId, "event-definitions"] as const,
  },

  sows: {
    all: (farmId: string) => ["sows", farmId] as const,
    list: (farmId: string, params?: Record<string, unknown>) =>
      ["sows", farmId, params] as const,
    detail: (farmId: string, sowId: string) =>
      ["sows", farmId, sowId] as const,
  },

  events: {
    matings: (farmId: string, sowId?: string) =>
      ["events", "matings", farmId, sowId] as const,
    farrowings: (farmId: string, sowId?: string) =>
      ["events", "farrowings", farmId, sowId] as const,
    weanings: (farmId: string, sowId?: string) =>
      ["events", "weanings", farmId, sowId] as const,
  },

  kpi: {
    dashboard: (farmId: string) => ["kpi", "dashboard", farmId] as const,
    trend: (farmId: string, kpi: string, months: number) =>
      ["kpi", "trend", farmId, kpi, months] as const,
  },

  chat: {
    history: (farmId: string) => ["chat", "history", farmId] as const,
  },

  alerts: {
    overdue: (farmId: string) => ["alerts", "overdue", farmId] as const,
    cullCandidates: (farmId: string) => ["alerts", "cull", farmId] as const,
  },
} as const;
