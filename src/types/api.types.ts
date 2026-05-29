// Auto-generated from PigOS OpenAPI v1 spec
// Reflects: docs/api/openapi-v1.yaml

// ─── Common ──────────────────────────────────────────────────────────────────

export interface ApiError {
  code: string;
  message: string;
  detail?: Record<string, unknown>;
}

export interface PageMeta {
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface PagedResult<T> {
  items: T[];
  meta: PageMeta;
}

// ─── Auth ─────────────────────────────────────────────────────────────────────

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user_id: string;
  name: string;
  email: string;
  role: "OWNER" | "MANAGER" | "WORKER" | "VET";
  farm_ids: string[];
}

export interface RefreshResponse {
  access_token: string;
  token_type: string;
}

export interface UserProfile {
  id: string;
  email: string;
  name: string;
  role: "OWNER" | "MANAGER" | "WORKER" | "VET";
  farm_ids: string[];
}

// ─── Onboarding ───────────────────────────────────────────────────────────────

export interface OnboardingRequest {
  org_name: string;
  country: string;
  name: string;
  email: string;
  password: string;
  farm_name: string;
  farm_type?: "SOW_FARM" | "FARROW_TO_FINISH" | "NURSERY" | "FINISHER" | "BOAR_STUD";
  sow_count?: number;
  timezone?: string;
}

export interface OnboardingResponse {
  org_id: string;
  farm_id: string;
  user_id: string;
  access_token: string;
  refresh_token: string;
}

// ─── Farms ────────────────────────────────────────────────────────────────────

export interface Farm {
  id: string;
  name: string;
  country: string;
  farm_type: string;
  sow_count: number;
  timezone: string;
  currency: string;
  created_at: string;
}

// ─── Sows ─────────────────────────────────────────────────────────────────────

export type SowStatus =
  | "ACTIVE"
  | "GESTATING"
  | "LACTATING"
  | "WEANED"
  | "DRY"
  | "CULLED"
  | "DEAD";

export interface Sow {
  id: string;
  ear_tag: string;
  status: SowStatus;
  parity: number;
  breed?: string;
  birth_date?: string;
  entry_date: string;
  notes?: string;
  farm_id: string;
  created_at: string;
  updated_at: string;
}

export type SowEntryType = "GILT" | "PURCHASE" | "TRANSFER" | "BORN";

export interface CreateSowRequest {
  ear_tag: string;
  entry_date: string;
  entry_type: SowEntryType;
  parity?: number;
  breed?: string;
  rfid_tag?: string;
  notes?: string;
}

export interface UpdateSowRequest {
  status?: SowStatus;
  notes?: string;
}

// ─── Events ───────────────────────────────────────────────────────────────────

export interface Mating {
  id: string;
  sow_id: string;
  mating_date: string;
  mating_type: "AI" | "NATURAL";
  mating_number: number;
  boar_id?: string;
  semen_batch?: string;
  notes?: string;
  farm_id: string;
  created_at: string;
}

export interface CreateMatingRequest {
  sow_id: string;
  mating_date: string;
  mating_type: "AI" | "NATURAL";
  mating_number?: number;
  boar_id?: string;
  semen_batch?: string;
  notes?: string;
}

export interface Farrowing {
  id: string;
  sow_id: string;
  farrowing_date: string;
  total_born: number;
  born_alive: number;
  born_dead: number;
  mummies: number;
  farrowing_type: string;
  notes?: string;
  farm_id: string;
  created_at: string;
}

export interface CreateFarrowingRequest {
  sow_id: string;
  farrowing_date: string;
  total_born: number;
  born_alive: number;
  born_dead?: number;
  mummies?: number;
  farrowing_type?: string;
  notes?: string;
}

export interface Weaning {
  id: string;
  sow_id: string;
  weaning_date: string;
  weaned_count: number;
  avg_weight_kg?: number;
  notes?: string;
  farm_id: string;
  created_at: string;
}

export interface CreateWeaningRequest {
  sow_id: string;
  weaning_date: string;
  weaned_count: number;
  avg_weight_kg?: number;
  notes?: string;
}

export interface ReproductiveEvent {
  id: string;
  sow_id: string;
  event_type: "RETURN_TO_ESTRUS" | "ABORTION" | "EMPTY" | "CULL" | "DEATH";
  event_date: string;
  notes?: string;
  farm_id: string;
  created_at: string;
}

export interface HealthEvent {
  id: string;
  sow_id?: string;
  event_date: string;
  disease_code?: string;
  vaccine_code?: string;
  active_substance?: string;
  dose_mg?: number;
  severity?: "MILD" | "MODERATE" | "SEVERE" | "CRITICAL";
  notes?: string;
  farm_id: string;
  created_at: string;
}

// ─── KPI ──────────────────────────────────────────────────────────────────────

export interface Alert {
  rule_id: string;
  kpi: string;
  severity: "OK" | "INFO" | "WARNING" | "CRITICAL";
  message: string;
  current_value?: number;
  target_value?: number;
}

export interface KpiDashboard {
  farm_id: string;
  as_of: string;
  psy: number | null;
  npd: number | null;
  farrowing_rate: number | null;
  active_sows: number;
  gestating: number;
  lactating: number;
  weaned: number;
  alerts: Alert[];
}

export interface KpiTrend {
  period: string;
  psy: number | null;
  npd: number | null;
  farrowing_rate: number | null;
}

// ─── Q&A / Chat ───────────────────────────────────────────────────────────────

export interface ChatQuery {
  question: string;
  locale?: "en" | "ko" | "es" | "zh";
}

export interface FindingOut {
  rule_id: string;
  kpi: string;
  severity: "OK" | "INFO" | "WARNING" | "CRITICAL";
  current_value: number | null;
  target_value: number | null;
  causes: string[];
  recommended_actions: string[];
}

export interface ChatResponse {
  intent: string;
  severity: "OK" | "INFO" | "WARNING" | "CRITICAL";
  answer: string;
  findings: FindingOut[];
  farm_id: string;
  as_of: string;
  renderer: "template" | "llm";
}

// ─── Offline Sync ─────────────────────────────────────────────────────────────

export interface SyncMating {
  id: string;
  sow_id: string;
  mating_date: string;
  mating_type: "AI" | "NATURAL";
  boar_id?: string;
  semen_batch?: string;
  mating_number?: number;
  notes?: string;
  client_created_at: string;
}

export interface SyncFarrowing {
  id: string;
  sow_id: string;
  farrowing_date: string;
  total_born: number;
  born_alive: number;
  born_dead?: number;
  mummies?: number;
  farrowing_type?: string;
  notes?: string;
  client_created_at: string;
}

export interface SyncWeaning {
  id: string;
  sow_id: string;
  weaning_date: string;
  weaned_count: number;
  avg_weight_kg?: number;
  notes?: string;
  client_created_at: string;
}

export interface SyncReproductiveEvent {
  id: string;
  sow_id: string;
  event_type: string;
  event_date: string;
  notes?: string;
  client_created_at: string;
}

export interface SyncHealthEvent {
  id: string;
  sow_id?: string;
  event_date: string;
  disease_code?: string;
  vaccine_code?: string;
  active_substance?: string;
  dose_mg?: number;
  severity?: string;
  notes?: string;
  client_created_at: string;
}

export interface SyncChanges {
  matings?: SyncMating[];
  farrowings?: SyncFarrowing[];
  weanings?: SyncWeaning[];
  reproductive_events?: SyncReproductiveEvent[];
  health_events?: SyncHealthEvent[];
}

export interface SyncRequest {
  farm_id: string;
  client_id: string;
  last_sync_at: string | null;
  changes: SyncChanges;
  dry_run?: boolean;
}

export interface SyncAccepted {
  id: string;
  entity: string;
  action: "created" | "merged";
}

export interface SyncRejected {
  id: string;
  entity: string;
  reason: string;
  detail: Record<string, unknown>;
}

export interface SyncConflict {
  id: string;
  entity: string;
  conflict_type: string;
  client_record: Record<string, unknown>;
  server_record: Record<string, unknown>;
}

export interface ServerChanges {
  sows: Record<string, unknown>[];
  matings: Record<string, unknown>[];
  farrowings: Record<string, unknown>[];
  weanings: Record<string, unknown>[];
  reproductive_events: Record<string, unknown>[];
  health_events: Record<string, unknown>[];
  period_locks: Record<string, unknown>[];
  deleted_ids: string[];
}

export interface SyncResponse {
  sync_token: string;
  dry_run: boolean;
  accepted: SyncAccepted[];
  rejected: SyncRejected[];
  conflicts: SyncConflict[];
  server_changes: ServerChanges;
  require_full_sync: boolean;
  stats: Record<string, number>;
}
