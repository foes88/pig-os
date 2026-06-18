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
    reproConfig: (farmId: string) => ["farms", farmId, "repro-config"] as const,
    members: (farmId: string) => ["farms", farmId, "members"] as const,
  },

  reports: {
    daily: (farmId: string, date: string) => ["reports", "daily", farmId, date] as const,
    reproduction: (farmId: string, start: string, end: string, period: string, groupBy = "period") =>
      ["reports", "reproduction", farmId, start, end, period, groupBy] as const,
    productionSummary: (farmId: string, start: string, end: string, period: string, groupBy = "period") =>
      ["reports", "production-summary", farmId, start, end, period, groupBy] as const,
    growFinish: (farmId: string, start: string, end: string) =>
      ["reports", "grow-finish", farmId, start, end] as const,
    sowHistory: (farmId: string, sowId: string) =>
      ["reports", "sow-history", farmId, sowId] as const,
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
    ledger: (farmId: string, kind?: string) =>
      ["events", "ledger", farmId, kind ?? "all"] as const,
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

  tasks: {
    list: (farmId: string, status: string) => ["tasks", farmId, status] as const,
  },

  notifications: {
    list: (farmId: string, unreadOnly: boolean) => ["notifications", farmId, unreadOnly] as const,
    unread: (farmId: string) => ["notifications", "unread", farmId] as const,
  },

  analytics: {
    prrsByGenetics: (farmId: string) => ["analytics", "prrs", farmId] as const,
  },

  thresholds: {
    list: (farmId: string) => ["thresholds", farmId] as const,
  },
} as const;
