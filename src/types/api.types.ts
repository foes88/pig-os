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

export interface FarmLocalConfig {
  weight_unit: "kg" | "lb";
  currency_code: string;
  currency_symbol: string;
  min_wean_period: number | null;
  requires_traceability: boolean;
  requires_antibiotic_tracking: boolean;
  slaughter_weight_target_kg: number | null;
  market_code: string | null;
}

export interface EventDefinition {
  event_code: string;
  category: string;
  label_en: string;
  label_ko: string | null;
  label_vi: string | null;
  required_fields: Record<string, string> | null;
  regional_applicability: string;
}

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

// docs/SCREEN_MENU_SPEC.md "Sow Status Definitions" 기준
export type SowStatus =
  | "GILT"      // 후보돈 — 입식, 미교배
  | "OPEN"      // 공태 — 이유 후 교배 대기
  | "PREGNANT"  // 임신
  | "LACTATING" // 포유
  | "ACCIDENT"  // 번식사고 — 재발/공태판정/유산, 재교배 대기
  | "CULLED"
  | "DEAD"
  | "SOLD"
  | "TRANSFER";

export interface Sow {
  id: string;
  farm_id: string;
  ear_tag: string;
  rfid_tag: string | null;
  status: SowStatus;
  parity: number;
  breed: string | null;
  breed_company: string | null;
  entry_date: string;
  entry_type: SowEntryType;
  building_id: string | null;
  deleted_at: string | null;
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
  ear_tag?: string;
  breed?: string;
  rfid_tag?: string;
  building_id?: string;
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
  farm_id: string;
  sow_id: string;
  mating_id: string | null;
  farrowing_date: string;
  total_born: number;
  born_alive: number;
  stillborn: number;
  mummified: number;
  farrowing_ease: "EASY" | "ASSISTED" | "DIFFICULT" | null;
  breeding_cycle_id: string | null;
  created_at: string;
}

export interface CreateFarrowingRequest {
  sow_id: string;
  mating_id?: string;
  farrowing_date: string;
  born_alive: number;
  stillborn?: number;
  mummified?: number;
  farrowing_ease?: "EASY" | "ASSISTED" | "DIFFICULT";
  notes?: string;
}

export interface Weaning {
  id: string;
  farm_id: string;
  sow_id: string;
  farrowing_id: string | null;
  weaning_date: string;
  weaned_count: number;
  weaning_age_days: number | null;
  avg_weaning_weight_kg: number | null;
  created_at: string;
}

export interface CreateWeaningRequest {
  sow_id: string;
  farrowing_id?: string;
  weaning_date: string;
  weaned_count: number;
  avg_weaning_weight_kg?: number;
  notes?: string;
}

export interface ReproductiveEvent {
  id: string;
  sow_id: string;
  event_type: "RETURN_TO_ESTRUS" | "ABORTION" | "EMPTY" | "INFERTILE" | "CULLED" | "DEAD" | "TRANSFER_OUT" | "SOLD" | "HEAT_DETECTED";
  event_date: string;
  mating_id?: string;
  detected_method?: "ULTRASOUND" | "VISUAL" | "BEHAVIOR" | "BLOOD_TEST";
  notes?: string;
  farm_id: string;
  created_at: string;
}

export interface CreateReproductiveEventRequest {
  sow_id: string;
  event_type: "RETURN_TO_ESTRUS" | "ABORTION" | "EMPTY" | "INFERTILE" | "CULLED" | "DEAD" | "TRANSFER_OUT" | "SOLD" | "HEAT_DETECTED";
  event_date: string;
  mating_id?: string;
  detected_method?: "ULTRASOUND" | "VISUAL" | "BEHAVIOR" | "BLOOD_TEST";
  notes?: string;
}

export interface SowCullRequest {
  removal_type: "CULLED" | "DEAD" | "SOLD" | "TRANSFER";
  removal_date: string;
  reason_category?: "REPRODUCTIVE" | "LAMENESS" | "DISEASE" | "AGE" | "PERFORMANCE" | "INJURY" | "BEHAVIOR" | "UNKNOWN" | "OTHER";
  reason_detail?: string;
  body_weight_kg?: number;
  sale_price?: number;
  sale_currency?: string;
  notes?: string;
}

export interface RemovalRecord {
  id: string;
  farm_id: string;
  sow_id: string;
  removal_date: string;
  removal_type: string;
  reason_category?: string;
  reason_detail?: string;
  body_weight_kg?: number;
  sale_price?: number;
  sale_currency?: string;
  created_at: string;
}

export interface CreatePigletEventRequest {
  sow_id: string;
  farrowing_id?: string;
  event_date: string;
  event_type: "STILLBORN_REMOVAL" | "DEATH" | "FOSTER_IN" | "FOSTER_OUT";
  piglet_count: number;
  reason?: "CRUSHING" | "SCOURS" | "STARVATION" | "CONGENITAL" | "HYPOTHERMIA" | "OTHER";
  target_sow_id?: string;
  notes?: string;
}

export interface PigletEventRecord {
  id: string;
  farm_id: string;
  farrowing_id: string;
  sow_id: string;
  event_date: string;
  event_type: string;
  piglet_count: number;
  reason?: string;
  created_at: string;
}

// ── Piglet Groups (자돈) ──────────────────────────────────────────────────────

export interface PigletGroup {
  id: string;
  farm_id: string;
  group_code: string;
  batch_name?: string;
  weaning_date: string;
  transfer_date?: string;
  transfer_type?: "FINISHER_TRANSFER" | "SOLD" | "CULLED";
  head_count_in: number;
  head_count_dead: number;
  head_count_out?: number;
  avg_entry_weight_kg?: number;
  avg_exit_weight_kg?: number;
  building_id?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface CreatePigletGroupRequest {
  group_code: string;
  batch_name?: string;
  weaning_date: string;
  head_count_in: number;
  avg_entry_weight_kg?: number;
  building_id?: string;
  notes?: string;
}

export interface PigletGroupTransferOutRequest {
  transfer_date: string;
  transfer_type: "FINISHER_TRANSFER" | "SOLD" | "CULLED";
  head_count_out: number;
  avg_exit_weight_kg?: number;
  notes?: string;
}

export interface PigletTransfer {
  id: string;
  farm_id: string;
  source_sow_id: string;
  dest_sow_id: string;
  transfer_date: string;
  piglet_count: number;
  source_farrowing_id?: string;
  dest_farrowing_id?: string;
  reason?: string;
  created_at: string;
}

export interface CreatePigletTransferRequest {
  source_sow_id: string;
  dest_sow_id: string;
  transfer_date: string;
  piglet_count: number;
  source_farrowing_id?: string;
  dest_farrowing_id?: string;
  reason?: string;
  notes?: string;
}

// ── Finisher Groups (비육돈) ──────────────────────────────────────────────────

export interface FinisherGroup {
  id: string;
  farm_id: string;
  group_code: string;
  batch_name?: string;
  start_date: string;
  end_date?: string;
  head_count_in: number;
  head_count_out?: number;
  avg_entry_weight_kg?: number;
  avg_exit_weight_kg?: number;
  building_id?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateFinisherGroupRequest {
  group_code: string;
  batch_name?: string;
  start_date: string;
  head_count_in: number;
  avg_entry_weight_kg?: number;
  building_id?: string;
  notes?: string;
}

export interface FinisherGroupShipRequest {
  end_date: string;
  head_count_out: number;
  avg_exit_weight_kg?: number;
  notes?: string;
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
  locale?: "en" | "ko" | "zh" | "es" | "vi";
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

export interface SyncPigletEvent {
  id: string;
  sow_id: string;
  farrowing_id?: string;
  event_date: string;
  event_type: "STILLBORN_REMOVAL" | "DEATH" | "FOSTER_IN" | "FOSTER_OUT";
  piglet_count: number;
  reason?: "CRUSHING" | "SCOURS" | "STARVATION" | "CONGENITAL" | "HYPOTHERMIA" | "OTHER";
  target_sow_id?: string;
  notes?: string;
  client_created_at: string;
}

export interface SyncChanges {
  matings?: SyncMating[];
  farrowings?: SyncFarrowing[];
  weanings?: SyncWeaning[];
  reproductive_events?: SyncReproductiveEvent[];
  health_events?: SyncHealthEvent[];
  piglet_events?: SyncPigletEvent[];
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
  piglet_events: Record<string, unknown>[];
  removals: Record<string, unknown>[];
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

// ── Alerts / Tasks (Phase 2 backend) ──────────────────────────────────────────

export type OverdueType =
  | "gilt_no_estrus"
  | "gilt_overdue_mating"
  | "pregnant_overdue_farrowing"
  | "lactating_overdue_weaning"
  | "open_overdue_mating"
  | "accident_overdue_mating";

export interface OverdueSow {
  type: OverdueType;
  sow_id: string;
  ear_tag: string;
  status: SowStatus;
  parity: number;
  overdue_days: number;
}

export interface OverdueSummary {
  total: number;
  counts: Record<string, number>;
  items: OverdueSow[];
}

export interface CullCandidate {
  sow_id: string;
  ear_tag: string;
  status: SowStatus;
  parity: number;
  reasons: string[];
  last_weaned: number | null;
}
