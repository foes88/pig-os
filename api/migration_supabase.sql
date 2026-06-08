BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> f36cde9d762c

CREATE TABLE audit_log (
    id UUID NOT NULL, 
    user_id UUID, 
    farm_id UUID, 
    action VARCHAR(20) NOT NULL, 
    entity_type VARCHAR(50) NOT NULL, 
    entity_id UUID, 
    old_value JSONB, 
    new_value JSONB, 
    ip_address INET, 
    user_agent TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

CREATE INDEX idx_audit_entity ON audit_log (entity_type, entity_id);

CREATE INDEX idx_audit_farm ON audit_log (farm_id, created_at);

CREATE TABLE compliance_profiles (
    profile_code VARCHAR(50) NOT NULL, 
    profile_name VARCHAR(100) NOT NULL, 
    requires_traceability BOOLEAN NOT NULL, 
    requires_welfare_metrics BOOLEAN NOT NULL, 
    requires_antibiotic_tracking BOOLEAN NOT NULL, 
    requires_env_reporting BOOLEAN NOT NULL, 
    min_wean_period INTEGER, 
    max_antibiotic_treatments NUMERIC(5, 2), 
    notes TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (profile_code)
);

CREATE TABLE default_metric_values (
    id SERIAL NOT NULL, 
    scope_type VARCHAR(20) NOT NULL, 
    scope_code VARCHAR(20) NOT NULL, 
    metric_code VARCHAR(50) NOT NULL, 
    default_value NUMERIC(10, 2), 
    benchmark_avg NUMERIC(10, 2), 
    benchmark_top25 NUMERIC(10, 2), 
    target_value NUMERIC(10, 2), 
    unit_code VARCHAR(20), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (scope_type, scope_code, metric_code)
);

CREATE INDEX idx_dmv_lookup ON default_metric_values (metric_code, scope_type, scope_code);

CREATE TABLE disease_codes (
    disease_code VARCHAR(20) NOT NULL, 
    woah_code VARCHAR(20), 
    label_en VARCHAR(100) NOT NULL, 
    label_ko VARCHAR(100), 
    label_vi VARCHAR(100), 
    category VARCHAR(20) NOT NULL, 
    notifiable BOOLEAN, 
    regional_prevalence JSONB, 
    typical_mortality_pct NUMERIC(5, 2), 
    typical_treatment TEXT, 
    PRIMARY KEY (disease_code)
);

CREATE TABLE event_definitions (
    event_code VARCHAR(30) NOT NULL, 
    category VARCHAR(20) NOT NULL, 
    label_en VARCHAR(100) NOT NULL, 
    label_ko VARCHAR(100), 
    label_vi VARCHAR(100), 
    required_fields JSONB, 
    regional_applicability VARCHAR(50), 
    phase VARCHAR(10), 
    sort_order INTEGER, 
    PRIMARY KEY (event_code)
);

CREATE TABLE market_defaults (
    market_code VARCHAR(10) NOT NULL, 
    market_name VARCHAR(50) NOT NULL, 
    weight_unit VARCHAR(5) NOT NULL, 
    currency_code VARCHAR(3) NOT NULL, 
    pricing_unit VARCHAR(20), 
    compliance_profile_code VARCHAR(50), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (market_code)
);

CREATE TABLE medication_catalog (
    active_substance VARCHAR(100) NOT NULL, 
    atcvet_code VARCHAR(10), 
    antibiotic_class VARCHAR(50), 
    ddda_mg_per_kg NUMERIC(10, 4), 
    standard_dose_mg_kg NUMERIC(10, 4), 
    withdrawal_days_meat INTEGER, 
    route VARCHAR(20), 
    vfd_required_us BOOLEAN, 
    eu_restricted BOOLEAN, 
    notes TEXT, 
    PRIMARY KEY (active_substance)
);

CREATE TABLE organizations (
    id UUID NOT NULL, 
    name VARCHAR(200) NOT NULL, 
    org_type VARCHAR(20) NOT NULL, 
    country VARCHAR(2) NOT NULL, 
    timezone VARCHAR(50) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id)
);

CREATE TABLE scope_kpi_recommendations (
    id SERIAL NOT NULL, 
    scope_type VARCHAR(20) NOT NULL, 
    scope_code VARCHAR(20) NOT NULL, 
    kpi_code VARCHAR(50) NOT NULL, 
    display_priority INTEGER NOT NULL, 
    is_base BOOLEAN NOT NULL, 
    is_addon BOOLEAN NOT NULL, 
    addon_code VARCHAR(50), 
    is_visible BOOLEAN NOT NULL, 
    farm_type VARCHAR(20), 
    min_sow_count INTEGER, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (scope_type, scope_code, kpi_code, farm_type, min_sow_count)
);

CREATE INDEX idx_skr_lookup ON scope_kpi_recommendations (scope_type, scope_code, display_priority);

CREATE TABLE vaccine_catalog (
    vaccine_code VARCHAR(30) NOT NULL, 
    disease_target VARCHAR(20), 
    vaccine_type VARCHAR(20), 
    product_name VARCHAR(100), 
    manufacturer VARCHAR(100), 
    approved_regions TEXT[], 
    route VARCHAR(20), 
    withdrawal_days INTEGER, 
    notes TEXT, 
    PRIMARY KEY (vaccine_code)
);

CREATE TABLE farms (
    id UUID NOT NULL, 
    org_id UUID NOT NULL, 
    farm_code VARCHAR(30) NOT NULL, 
    name VARCHAR(200) NOT NULL, 
    country VARCHAR(2) NOT NULL, 
    region VARCHAR(100), 
    gps_lat FLOAT, 
    gps_lng FLOAT, 
    timezone VARCHAR(50) NOT NULL, 
    unit_system VARCHAR(10) NOT NULL, 
    language VARCHAR(5) NOT NULL, 
    currency VARCHAR(3) NOT NULL, 
    date_format VARCHAR(15) NOT NULL, 
    notification_channel VARCHAR(20) NOT NULL, 
    farm_scale VARCHAR(15) NOT NULL, 
    internet_reliability VARCHAR(10) NOT NULL, 
    active BOOLEAN NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(org_id) REFERENCES organizations (id), 
    UNIQUE (farm_code)
);

CREATE INDEX idx_farms_country ON farms (country);

CREATE INDEX idx_farms_org ON farms (org_id);

CREATE TABLE region_defaults (
    region_code VARCHAR(10) NOT NULL, 
    region_name VARCHAR(50) NOT NULL, 
    market_code VARCHAR(10) NOT NULL, 
    weight_unit VARCHAR(5), 
    currency_code VARCHAR(3), 
    pricing_unit VARCHAR(20), 
    compliance_profile_code VARCHAR(50), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (region_code), 
    FOREIGN KEY(market_code) REFERENCES market_defaults (market_code)
);

CREATE TABLE users (
    id UUID NOT NULL, 
    org_id UUID, 
    email VARCHAR(255), 
    phone VARCHAR(30), 
    name VARCHAR(100) NOT NULL, 
    password_hash VARCHAR(255) NOT NULL, 
    role VARCHAR(30) NOT NULL, 
    language VARCHAR(5) NOT NULL, 
    active BOOLEAN NOT NULL, 
    last_login_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(org_id) REFERENCES organizations (id), 
    UNIQUE (email)
);

CREATE TABLE addon_subscriptions (
    id UUID NOT NULL, 
    farm_id UUID NOT NULL, 
    addon_code VARCHAR(50) NOT NULL, 
    is_active BOOLEAN NOT NULL, 
    started_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    cancelled_at TIMESTAMP WITH TIME ZONE, 
    plan_price_usd FLOAT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(farm_id) REFERENCES farms (id), 
    CONSTRAINT uq_farm_addon UNIQUE (farm_id, addon_code)
);

CREATE INDEX idx_addon_sub_farm ON addon_subscriptions (farm_id, is_active);

CREATE TABLE api_keys (
    id UUID NOT NULL, 
    org_id UUID NOT NULL, 
    name VARCHAR(100) NOT NULL, 
    key_prefix VARCHAR(8) NOT NULL, 
    key_hash VARCHAR(255) NOT NULL, 
    scopes VARCHAR[] NOT NULL, 
    rate_limit_per_min INTEGER NOT NULL, 
    expires_at TIMESTAMP WITH TIME ZONE, 
    last_used_at TIMESTAMP WITH TIME ZONE, 
    is_active BOOLEAN NOT NULL, 
    created_by UUID, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    revoked_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(created_by) REFERENCES users (id), 
    FOREIGN KEY(org_id) REFERENCES organizations (id), 
    UNIQUE (key_hash)
);

CREATE INDEX idx_api_keys_org ON api_keys (org_id) WHERE is_active = TRUE;

CREATE TABLE boars (
    id UUID NOT NULL, 
    farm_id UUID NOT NULL, 
    ear_tag VARCHAR(30) NOT NULL, 
    breed VARCHAR(50), 
    breed_company VARCHAR(30), 
    status VARCHAR(20) NOT NULL, 
    entry_date TIMESTAMP WITH TIME ZONE NOT NULL, 
    entry_type VARCHAR(20), 
    semen_quality VARCHAR(20), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(farm_id) REFERENCES farms (id), 
    UNIQUE (farm_id, ear_tag)
);

CREATE TABLE buildings (
    id UUID NOT NULL, 
    farm_id UUID NOT NULL, 
    name VARCHAR(100) NOT NULL, 
    building_type VARCHAR(30) NOT NULL, 
    floor_number INTEGER NOT NULL, 
    capacity INTEGER, 
    housing_type VARCHAR(20) NOT NULL, 
    area_per_pig_m2 NUMERIC(5, 2), 
    area_per_pig_sqft NUMERIC(5, 2), 
    prop12_compliant BOOLEAN, 
    welfare_enrichment VARCHAR(100), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(farm_id) REFERENCES farms (id)
);

CREATE INDEX idx_buildings_farm ON buildings (farm_id);

CREATE TABLE farm_configs (
    id UUID NOT NULL, 
    farm_id UUID NOT NULL, 
    config_key VARCHAR(50) NOT NULL, 
    config_value VARCHAR(100) NOT NULL, 
    description TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(farm_id) REFERENCES farms (id), 
    UNIQUE (farm_id, config_key)
);

CREATE TABLE kpi_snapshots (
    id UUID NOT NULL, 
    farm_id UUID NOT NULL, 
    period_type VARCHAR(10) NOT NULL, 
    period_start DATE NOT NULL, 
    period_end DATE NOT NULL, 
    psy NUMERIC(6, 2), 
    msy NUMERIC(6, 2), 
    npd NUMERIC(6, 2), 
    mortality_rate NUMERIC(5, 2), 
    fcr NUMERIC(5, 3), 
    avg_daily_gain NUMERIC(6, 2), 
    active_sow_count INTEGER, 
    gestating_count INTEGER, 
    lactating_count INTEGER, 
    is_stale BOOLEAN NOT NULL, 
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(farm_id) REFERENCES farms (id), 
    UNIQUE (farm_id, period_type, period_start)
);

CREATE INDEX idx_kpi_snap_farm_period ON kpi_snapshots (farm_id, period_type, period_start);

CREATE INDEX idx_kpi_snap_stale ON kpi_snapshots (is_stale) WHERE is_stale = TRUE;

CREATE TABLE market_price_reference (
    id SERIAL NOT NULL, 
    region_code VARCHAR(10), 
    market_code VARCHAR(10), 
    price_type VARCHAR(30) NOT NULL, 
    price_value NUMERIC(12, 4) NOT NULL, 
    currency_code VARCHAR(3) NOT NULL, 
    weight_unit VARCHAR(5) NOT NULL, 
    price_date DATE NOT NULL, 
    source VARCHAR(100), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(market_code) REFERENCES market_defaults (market_code), 
    FOREIGN KEY(region_code) REFERENCES region_defaults (region_code)
);

CREATE INDEX idx_mpr_market_date ON market_price_reference (market_code, price_date);

CREATE INDEX idx_mpr_region_date ON market_price_reference (region_code, price_date);

CREATE TABLE notifications (
    id UUID NOT NULL, 
    farm_id UUID, 
    user_id UUID NOT NULL, 
    type VARCHAR(20) NOT NULL, 
    channel VARCHAR(30), 
    title VARCHAR(200) NOT NULL, 
    body TEXT NOT NULL, 
    alert_type VARCHAR(50), 
    severity VARCHAR(10), 
    related_entity_type VARCHAR(50), 
    related_entity_id UUID, 
    sent_at TIMESTAMP WITH TIME ZONE, 
    read_at TIMESTAMP WITH TIME ZONE, 
    failed_at TIMESTAMP WITH TIME ZONE, 
    failure_reason TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(farm_id) REFERENCES farms (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX idx_notif_farm ON notifications (farm_id, created_at) WHERE farm_id IS NOT NULL;

CREATE INDEX idx_notif_user_unread ON notifications (user_id, created_at) WHERE read_at IS NULL;

CREATE TABLE period_locks (
    id UUID NOT NULL, 
    farm_id UUID NOT NULL, 
    period_year SMALLINT NOT NULL, 
    period_month SMALLINT NOT NULL, 
    locked_by UUID NOT NULL, 
    locked_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    unlocked_by UUID, 
    unlocked_at TIMESTAMP WITH TIME ZONE, 
    note TEXT, 
    PRIMARY KEY (id), 
    FOREIGN KEY(farm_id) REFERENCES farms (id), 
    FOREIGN KEY(locked_by) REFERENCES users (id), 
    FOREIGN KEY(unlocked_by) REFERENCES users (id), 
    UNIQUE (farm_id, period_year, period_month)
);

CREATE INDEX idx_period_locks_farm ON period_locks (farm_id, period_year, period_month);

CREATE TABLE refresh_tokens (
    id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    token_hash VARCHAR(255) NOT NULL, 
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    revoked BOOLEAN NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id), 
    UNIQUE (token_hash)
);

CREATE INDEX idx_refresh_user ON refresh_tokens (user_id);

CREATE TABLE sync_conflict_queue (
    id UUID NOT NULL, 
    farm_id UUID NOT NULL, 
    client_id UUID NOT NULL, 
    entity VARCHAR(50) NOT NULL, 
    conflict_type VARCHAR(30) NOT NULL, 
    client_record JSONB NOT NULL, 
    server_record JSONB NOT NULL, 
    resolved_at TIMESTAMP WITH TIME ZONE, 
    resolution VARCHAR(20), 
    resolved_by UUID, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(farm_id) REFERENCES farms (id), 
    FOREIGN KEY(resolved_by) REFERENCES users (id)
);

CREATE INDEX idx_conflict_queue_farm_all ON sync_conflict_queue (farm_id, created_at);

CREATE INDEX idx_conflict_queue_farm_unresolved ON sync_conflict_queue (farm_id, created_at) WHERE resolved_at IS NULL;

CREATE TABLE sync_logs (
    id UUID NOT NULL, 
    farm_id UUID NOT NULL, 
    device_id VARCHAR(100) NOT NULL, 
    user_id UUID, 
    sync_direction VARCHAR(15) NOT NULL, 
    started_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    completed_at TIMESTAMP WITH TIME ZONE, 
    records_pushed INTEGER NOT NULL, 
    records_pulled INTEGER NOT NULL, 
    conflicts_found INTEGER NOT NULL, 
    conflicts_resolved INTEGER NOT NULL, 
    error_count INTEGER NOT NULL, 
    error_detail JSONB, 
    duration_ms INTEGER, 
    PRIMARY KEY (id), 
    FOREIGN KEY(farm_id) REFERENCES farms (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX idx_sync_logs_device ON sync_logs (device_id, started_at);

CREATE INDEX idx_sync_logs_farm ON sync_logs (farm_id, started_at);

CREATE TABLE sync_queue (
    id UUID NOT NULL, 
    farm_id UUID NOT NULL, 
    user_id UUID NOT NULL, 
    device_id VARCHAR(100) NOT NULL, 
    entity_type VARCHAR(50) NOT NULL, 
    entity_id UUID NOT NULL, 
    operation VARCHAR(10) NOT NULL, 
    payload JSONB NOT NULL, 
    offline_created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    synced_at TIMESTAMP WITH TIME ZONE, 
    conflict BOOLEAN NOT NULL, 
    conflict_resolution VARCHAR(20), 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(farm_id) REFERENCES farms (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX idx_sync_farm_pending ON sync_queue (farm_id) WHERE synced_at IS NULL;

CREATE TABLE user_farms (
    user_id UUID NOT NULL, 
    farm_id UUID NOT NULL, 
    role_override VARCHAR(30), 
    PRIMARY KEY (user_id, farm_id), 
    FOREIGN KEY(farm_id) REFERENCES farms (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE finisher_groups (
    id UUID NOT NULL, 
    farm_id UUID NOT NULL, 
    building_id UUID, 
    group_code VARCHAR(30) NOT NULL, 
    batch_name VARCHAR(100), 
    start_date DATE NOT NULL, 
    end_date DATE, 
    head_count_in INTEGER NOT NULL, 
    head_count_out INTEGER, 
    avg_entry_weight_kg NUMERIC(6, 2), 
    avg_exit_weight_kg NUMERIC(6, 2), 
    notes TEXT, 
    created_by UUID, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    deleted_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(building_id) REFERENCES buildings (id), 
    FOREIGN KEY(created_by) REFERENCES users (id), 
    FOREIGN KEY(farm_id) REFERENCES farms (id), 
    UNIQUE (farm_id, group_code)
);

CREATE INDEX idx_fg_farm_active ON finisher_groups (farm_id, start_date) WHERE deleted_at IS NULL;

CREATE TABLE sows (
    id UUID NOT NULL, 
    farm_id UUID NOT NULL, 
    building_id UUID, 
    ear_tag VARCHAR(30) NOT NULL, 
    rfid_tag VARCHAR(50), 
    parity INTEGER NOT NULL, 
    breed VARCHAR(50), 
    breed_company VARCHAR(30), 
    genetics_id VARCHAR(50), 
    status VARCHAR(20) NOT NULL, 
    entry_date TIMESTAMP WITH TIME ZONE NOT NULL, 
    entry_type VARCHAR(20) NOT NULL, 
    source_farm_id UUID, 
    exit_date TIMESTAMP WITH TIME ZONE, 
    stall_to_group_converted BOOLEAN, 
    nurse_sow_flag BOOLEAN NOT NULL, 
    ractopamine_free BOOLEAN NOT NULL, 
    deleted_at TIMESTAMP WITH TIME ZONE, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(building_id) REFERENCES buildings (id), 
    FOREIGN KEY(farm_id) REFERENCES farms (id), 
    UNIQUE (farm_id, ear_tag)
);

CREATE INDEX idx_sow_exit ON sows (exit_date) WHERE exit_date IS NOT NULL;

CREATE INDEX idx_sows_farm_status ON sows (farm_id, status);

CREATE INDEX idx_sows_parity ON sows (farm_id, parity);

CREATE TABLE breeding_cycles (
    id UUID NOT NULL, 
    farm_id UUID NOT NULL, 
    sow_id UUID NOT NULL, 
    parity INTEGER NOT NULL, 
    cycle_status VARCHAR(20) NOT NULL, 
    started_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    ended_at TIMESTAMP WITH TIME ZONE, 
    mating_count INTEGER NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(farm_id) REFERENCES farms (id), 
    FOREIGN KEY(sow_id) REFERENCES sows (id)
);

CREATE INDEX idx_bc_farm_sow ON breeding_cycles (farm_id, sow_id);

CREATE INDEX idx_bc_sow_parity ON breeding_cycles (sow_id, parity);

CREATE TABLE feed_records (
    id UUID NOT NULL, 
    farm_id UUID NOT NULL, 
    sow_id UUID, 
    group_id UUID, 
    building_id UUID, 
    record_date DATE NOT NULL, 
    feed_type VARCHAR(50), 
    quantity_kg NUMERIC(10, 3) NOT NULL, 
    unit_cost NUMERIC(10, 4), 
    currency VARCHAR(3), 
    notes TEXT, 
    created_by UUID, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    deleted_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(building_id) REFERENCES buildings (id), 
    FOREIGN KEY(created_by) REFERENCES users (id), 
    FOREIGN KEY(farm_id) REFERENCES farms (id), 
    FOREIGN KEY(sow_id) REFERENCES sows (id)
);

CREATE INDEX idx_feed_farm_date ON feed_records (farm_id, record_date);

CREATE TABLE health_events (
    id UUID NOT NULL, 
    farm_id UUID NOT NULL, 
    sow_id UUID, 
    group_id UUID, 
    event_date DATE NOT NULL, 
    event_type VARCHAR(30) NOT NULL, 
    disease_code VARCHAR(50), 
    severity VARCHAR(20), 
    treatment VARCHAR(200), 
    drug_code VARCHAR(50), 
    dose_ml NUMERIC(8, 2), 
    withdrawal_days INTEGER, 
    head_count INTEGER, 
    notes TEXT, 
    created_by UUID, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    deleted_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(created_by) REFERENCES users (id), 
    FOREIGN KEY(farm_id) REFERENCES farms (id), 
    FOREIGN KEY(sow_id) REFERENCES sows (id)
);

CREATE INDEX idx_health_farm_date ON health_events (farm_id, event_date);

CREATE TABLE removals (
    id UUID NOT NULL, 
    farm_id UUID NOT NULL, 
    sow_id UUID NOT NULL, 
    removal_date DATE NOT NULL, 
    removal_type VARCHAR(20) NOT NULL, 
    reason_category VARCHAR(30), 
    reason_detail TEXT, 
    body_weight_kg NUMERIC(6, 2), 
    sale_price NUMERIC(12, 2), 
    sale_currency VARCHAR(3), 
    created_by UUID, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    deleted_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(created_by) REFERENCES users (id), 
    FOREIGN KEY(farm_id) REFERENCES farms (id), 
    FOREIGN KEY(sow_id) REFERENCES sows (id)
);

CREATE INDEX idx_removals_farm_date ON removals (farm_id, removal_date);

CREATE TABLE matings (
    id UUID NOT NULL, 
    farm_id UUID NOT NULL, 
    sow_id UUID NOT NULL, 
    boar_id UUID, 
    breeding_cycle_id UUID, 
    mating_date DATE NOT NULL, 
    mating_type VARCHAR(10) NOT NULL, 
    mating_number INTEGER NOT NULL, 
    semen_batch VARCHAR(50), 
    notes TEXT, 
    created_by UUID, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    deleted_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(boar_id) REFERENCES boars (id), 
    FOREIGN KEY(breeding_cycle_id) REFERENCES breeding_cycles (id), 
    FOREIGN KEY(created_by) REFERENCES users (id), 
    FOREIGN KEY(farm_id) REFERENCES farms (id), 
    FOREIGN KEY(sow_id) REFERENCES sows (id)
);

CREATE INDEX idx_matings_date ON matings (farm_id, mating_date);

CREATE INDEX idx_matings_farm_sow ON matings (farm_id, sow_id);

CREATE TABLE farrowings (
    id UUID NOT NULL, 
    farm_id UUID NOT NULL, 
    sow_id UUID NOT NULL, 
    mating_id UUID NOT NULL, 
    breeding_cycle_id UUID, 
    farrowing_date DATE NOT NULL, 
    total_born INTEGER NOT NULL, 
    born_alive INTEGER NOT NULL, 
    stillborn INTEGER NOT NULL, 
    mummified INTEGER NOT NULL, 
    farrowing_ease VARCHAR(20), 
    notes TEXT, 
    created_by UUID, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    deleted_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(breeding_cycle_id) REFERENCES breeding_cycles (id), 
    FOREIGN KEY(created_by) REFERENCES users (id), 
    FOREIGN KEY(farm_id) REFERENCES farms (id), 
    FOREIGN KEY(mating_id) REFERENCES matings (id), 
    FOREIGN KEY(sow_id) REFERENCES sows (id)
);

CREATE INDEX idx_farrowings_date ON farrowings (farm_id, farrowing_date);

CREATE INDEX idx_farrowings_farm_sow ON farrowings (farm_id, sow_id);

CREATE TABLE pregnancy_checks (
    id UUID NOT NULL, 
    farm_id UUID NOT NULL, 
    sow_id UUID NOT NULL, 
    mating_id UUID, 
    check_date DATE NOT NULL, 
    days_after_mating INTEGER, 
    result VARCHAR(20) NOT NULL, 
    method VARCHAR(30), 
    notes TEXT, 
    created_by UUID, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    deleted_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(created_by) REFERENCES users (id), 
    FOREIGN KEY(farm_id) REFERENCES farms (id), 
    FOREIGN KEY(mating_id) REFERENCES matings (id), 
    FOREIGN KEY(sow_id) REFERENCES sows (id)
);

CREATE INDEX idx_pc_farm ON pregnancy_checks (farm_id);

CREATE TABLE reproductive_events (
    id UUID NOT NULL, 
    farm_id UUID NOT NULL, 
    sow_id UUID NOT NULL, 
    mating_id UUID, 
    breeding_cycle_id UUID, 
    event_date DATE NOT NULL, 
    event_type VARCHAR(30) NOT NULL, 
    detected_method VARCHAR(20), 
    notes TEXT, 
    created_by UUID, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    deleted_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(breeding_cycle_id) REFERENCES breeding_cycles (id), 
    FOREIGN KEY(created_by) REFERENCES users (id), 
    FOREIGN KEY(farm_id) REFERENCES farms (id), 
    FOREIGN KEY(mating_id) REFERENCES matings (id), 
    FOREIGN KEY(sow_id) REFERENCES sows (id)
);

CREATE INDEX idx_re_farm_sow ON reproductive_events (farm_id, sow_id);

CREATE INDEX idx_re_mating ON reproductive_events (mating_id) WHERE mating_id IS NOT NULL;

CREATE TABLE piglet_events (
    id UUID NOT NULL, 
    farm_id UUID NOT NULL, 
    farrowing_id UUID NOT NULL, 
    sow_id UUID NOT NULL, 
    event_date DATE NOT NULL, 
    event_type VARCHAR(20) NOT NULL, 
    piglet_count INTEGER NOT NULL, 
    reason VARCHAR(50), 
    target_sow_id UUID, 
    target_farrowing_id UUID, 
    notes TEXT, 
    created_by UUID, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    deleted_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(created_by) REFERENCES users (id), 
    FOREIGN KEY(farm_id) REFERENCES farms (id), 
    FOREIGN KEY(farrowing_id) REFERENCES farrowings (id), 
    FOREIGN KEY(sow_id) REFERENCES sows (id), 
    FOREIGN KEY(target_farrowing_id) REFERENCES farrowings (id), 
    FOREIGN KEY(target_sow_id) REFERENCES sows (id)
);

CREATE INDEX idx_pe_farm_date ON piglet_events (farm_id, event_date);

CREATE INDEX idx_pe_farrowing ON piglet_events (farrowing_id);

CREATE TABLE weanings (
    id UUID NOT NULL, 
    farm_id UUID NOT NULL, 
    sow_id UUID NOT NULL, 
    farrowing_id UUID NOT NULL, 
    breeding_cycle_id UUID, 
    weaning_date DATE NOT NULL, 
    weaned_count INTEGER NOT NULL, 
    weaning_age_days INTEGER, 
    avg_weaning_weight_kg FLOAT, 
    notes TEXT, 
    created_by UUID, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    deleted_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(breeding_cycle_id) REFERENCES breeding_cycles (id), 
    FOREIGN KEY(created_by) REFERENCES users (id), 
    FOREIGN KEY(farm_id) REFERENCES farms (id), 
    FOREIGN KEY(farrowing_id) REFERENCES farrowings (id), 
    FOREIGN KEY(sow_id) REFERENCES sows (id)
);

CREATE INDEX idx_weanings_farm_sow ON weanings (farm_id, sow_id);

INSERT INTO alembic_version (version_num) VALUES ('f36cde9d762c') RETURNING alembic_version.version_num;

-- Running upgrade f36cde9d762c -> a7cda1c25637

CREATE TABLE piglet_groups (
    id UUID NOT NULL, 
    farm_id UUID NOT NULL, 
    building_id UUID, 
    group_code VARCHAR(30) NOT NULL, 
    batch_name VARCHAR(100), 
    weaning_date DATE NOT NULL, 
    head_count_in INTEGER NOT NULL, 
    head_count_dead INTEGER NOT NULL, 
    head_count_out INTEGER, 
    avg_entry_weight_kg NUMERIC(6, 2), 
    avg_exit_weight_kg NUMERIC(6, 2), 
    transfer_date DATE, 
    transfer_type VARCHAR(20), 
    notes TEXT, 
    created_by UUID, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    deleted_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(building_id) REFERENCES buildings (id), 
    FOREIGN KEY(created_by) REFERENCES users (id), 
    FOREIGN KEY(farm_id) REFERENCES farms (id), 
    UNIQUE (farm_id, group_code)
);

CREATE INDEX idx_pg_farm_active ON piglet_groups (farm_id, weaning_date) WHERE deleted_at IS NULL;

UPDATE alembic_version SET version_num='a7cda1c25637' WHERE alembic_version.version_num = 'f36cde9d762c';

-- Running upgrade a7cda1c25637 -> 1cbe4adb7e13

CREATE TABLE piglet_transfers (
    id UUID NOT NULL, 
    farm_id UUID NOT NULL, 
    source_sow_id UUID NOT NULL, 
    dest_sow_id UUID NOT NULL, 
    source_farrowing_id UUID, 
    dest_farrowing_id UUID, 
    transfer_date DATE NOT NULL, 
    piglet_count INTEGER NOT NULL, 
    reason VARCHAR(100), 
    notes TEXT, 
    created_by UUID, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(created_by) REFERENCES users (id), 
    FOREIGN KEY(dest_farrowing_id) REFERENCES farrowings (id), 
    FOREIGN KEY(dest_sow_id) REFERENCES sows (id), 
    FOREIGN KEY(farm_id) REFERENCES farms (id), 
    FOREIGN KEY(source_farrowing_id) REFERENCES farrowings (id), 
    FOREIGN KEY(source_sow_id) REFERENCES sows (id)
);

CREATE INDEX idx_pt_dest_sow ON piglet_transfers (dest_sow_id);

CREATE INDEX idx_pt_farm_date ON piglet_transfers (farm_id, transfer_date);

CREATE INDEX idx_pt_source_sow ON piglet_transfers (source_sow_id);

UPDATE alembic_version SET version_num='1cbe4adb7e13' WHERE alembic_version.version_num = 'a7cda1c25637';

-- Running upgrade 1cbe4adb7e13 -> 6cbf1c758818

CREATE TABLE pilot_signups (
    id UUID DEFAULT gen_random_uuid() NOT NULL, 
    name VARCHAR(200) NOT NULL, 
    email VARCHAR(320) NOT NULL, 
    farm_size VARCHAR(20) NOT NULL, 
    country VARCHAR(100) NOT NULL, 
    role VARCHAR(20) NOT NULL, 
    lang VARCHAR(5) DEFAULT 'en' NOT NULL, 
    status VARCHAR(20) DEFAULT 'pending' NOT NULL, 
    notes TEXT, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT ck_pilot_signups_farm_size CHECK (farm_size IN ('under_100','100_500','500_1000','1000_plus')), 
    CONSTRAINT ck_pilot_signups_role CHECK (role IN ('owner','manager','vet','partner')), 
    CONSTRAINT ck_pilot_signups_status CHECK (status IN ('pending','contacted','onboarded','rejected'))
);

CREATE UNIQUE INDEX idx_pilot_signups_email ON pilot_signups (lower(email));

UPDATE alembic_version SET version_num='6cbf1c758818' WHERE alembic_version.version_num = '1cbe4adb7e13';

-- Running upgrade 6cbf1c758818 -> a1273623b95d

ALTER TABLE organizations ADD COLUMN parent_org_id UUID;

ALTER TABLE organizations ADD FOREIGN KEY(parent_org_id) REFERENCES organizations (id);

ALTER TABLE organizations ADD COLUMN org_level SMALLINT DEFAULT '0' NOT NULL;

CREATE INDEX idx_org_parent ON organizations (parent_org_id) WHERE parent_org_id IS NOT NULL;

ALTER TABLE users ADD COLUMN system_role VARCHAR(30) DEFAULT 'FARM_OWNER' NOT NULL;

UPDATE users
        SET system_role = CASE
            WHEN role = 'ADMIN' THEN 'SUPER_ADMIN'
            WHEN role = 'COMPANY' THEN 'VENDOR_ADMIN'
            WHEN role IN (
                'SUPER_ADMIN',
                'VENDOR_ADMIN',
                'DISTRIBUTOR_ADMIN',
                'DEALER_ADMIN',
                'FARM_OWNER',
                'FARM_MANAGER',
                'FARM_WORKER',
                'VET',
                'VIEWER',
                'API_CLIENT'
            ) THEN role
            ELSE 'FARM_OWNER'
        END;

CREATE INDEX idx_users_system_role ON users (system_role);

UPDATE alembic_version SET version_num='a1273623b95d' WHERE alembic_version.version_num = '6cbf1c758818';

-- Running upgrade a1273623b95d -> b6f6e3a9c2d1

INSERT INTO default_metric_values
            (scope_type, scope_code, metric_code, default_value, benchmark_avg,
             benchmark_top25, target_value, unit_code)
        VALUES
            ('system', 'SYSTEM', 'PSY',       22.00, 24.30, 27.00, 28.00, 'piglets/sow/year'),
            ('system', 'SYSTEM', 'MSY',       20.00, 22.00, 25.00, 26.00, 'piglets/sow/year'),
            ('system', 'SYSTEM', 'NPD',       35.00, 30.00, 22.00, 20.00, 'days'),
            ('system', 'SYSTEM', 'FCR',        2.80,  2.60,  2.40,  2.30, 'ratio'),
            ('system', 'SYSTEM', 'MORTALITY',  5.00,  4.00,  2.50,  2.00, '%'),
            ('region', 'KR',     'PSY',       22.00, 24.30, 27.00, 28.00, 'piglets/sow/year'),
            ('region', 'KR',     'MSY',       20.00, 22.10, 25.00, 26.00, 'piglets/sow/year'),
            ('region', 'KR',     'NPD',       35.00, 31.00, 22.00, 20.00, 'days')
        ON CONFLICT (scope_type, scope_code, metric_code) DO UPDATE
        SET default_value = EXCLUDED.default_value,
            benchmark_avg = EXCLUDED.benchmark_avg,
            benchmark_top25 = EXCLUDED.benchmark_top25,
            target_value = EXCLUDED.target_value,
            unit_code = EXCLUDED.unit_code,
            updated_at = NOW();

CREATE OR REPLACE FUNCTION effective_metric_values(
            p_farm_code VARCHAR,
            p_region_code VARCHAR,
            p_market_code VARCHAR
        )
        RETURNS TABLE (
            metric_code VARCHAR,
            default_value DECIMAL,
            benchmark_avg DECIMAL,
            benchmark_top25 DECIMAL,
            target_value DECIMAL,
            unit_code VARCHAR,
            scope_type VARCHAR
        ) AS $$
            SELECT DISTINCT ON (dmv.metric_code)
                dmv.metric_code,
                dmv.default_value,
                dmv.benchmark_avg,
                dmv.benchmark_top25,
                dmv.target_value,
                dmv.unit_code,
                dmv.scope_type
            FROM default_metric_values dmv
            WHERE (dmv.scope_type = 'farm'   AND dmv.scope_code = p_farm_code)
               OR (dmv.scope_type = 'region' AND dmv.scope_code = p_region_code)
               OR (dmv.scope_type = 'market' AND dmv.scope_code = p_market_code)
               OR (dmv.scope_type = 'system' AND dmv.scope_code = 'SYSTEM')
            ORDER BY
                dmv.metric_code,
                CASE dmv.scope_type
                    WHEN 'farm' THEN 1
                    WHEN 'region' THEN 2
                    WHEN 'market' THEN 3
                    WHEN 'system' THEN 4
                    ELSE 5
                END
        $$ LANGUAGE SQL STABLE;

CREATE OR REPLACE VIEW v_farm_psy AS
        SELECT
            s.farm_id,
            DATE_TRUNC('year', w.weaning_date)::DATE AS year_start,
            COUNT(DISTINCT s.id) AS avg_sow_count,
            COALESCE(SUM(w.weaned_count), 0) AS total_weaned,
            ROUND(
                COALESCE(SUM(w.weaned_count), 0)::NUMERIC
                / NULLIF(COUNT(DISTINCT s.id), 0),
                2
            ) AS psy
        FROM sows s
        LEFT JOIN weanings w
            ON w.sow_id = s.id
           AND w.deleted_at IS NULL
        WHERE s.deleted_at IS NULL
        GROUP BY s.farm_id, DATE_TRUNC('year', w.weaning_date)::DATE;

CREATE OR REPLACE VIEW v_sow_npd AS
        SELECT
            s.id AS sow_id,
            s.farm_id,
            w.id AS weaning_id,
            w.weaning_date,
            m_next.mating_date AS next_mating_date,
            (m_next.mating_date - w.weaning_date) AS wei_days
        FROM sows s
        JOIN weanings w
            ON w.sow_id = s.id
           AND w.deleted_at IS NULL
        LEFT JOIN LATERAL (
            SELECT m.mating_date
            FROM matings m
            WHERE m.sow_id = s.id
              AND m.mating_date > w.weaning_date
              AND m.mating_date <= w.weaning_date + INTERVAL '60 days'
              AND m.deleted_at IS NULL
            ORDER BY m.mating_date ASC
            LIMIT 1
        ) m_next ON TRUE
        WHERE s.deleted_at IS NULL;

UPDATE alembic_version SET version_num='b6f6e3a9c2d1' WHERE alembic_version.version_num = 'a1273623b95d';

-- Running upgrade b6f6e3a9c2d1 -> c7d4e2a1f9b0

ALTER TABLE default_metric_values ALTER COLUMN scope_code TYPE VARCHAR(50);

ALTER TABLE scope_kpi_recommendations ALTER COLUMN scope_code TYPE VARCHAR(50);

UPDATE alembic_version SET version_num='c7d4e2a1f9b0' WHERE alembic_version.version_num = 'b6f6e3a9c2d1';

-- Running upgrade c7d4e2a1f9b0 -> e3f9a2b4c8d1

ALTER TABLE default_metric_values
        ADD COLUMN IF NOT EXISTS warning_threshold  DECIMAL(10,2),
        ADD COLUMN IF NOT EXISTS critical_threshold DECIMAL(10,2),
        ADD COLUMN IF NOT EXISTS alert_direction    VARCHAR(10) NOT NULL DEFAULT 'below';

DROP FUNCTION IF EXISTS effective_metric_values(VARCHAR, VARCHAR, VARCHAR);

CREATE OR REPLACE FUNCTION effective_metric_values(
            p_farm_code   VARCHAR,
            p_region_code VARCHAR,
            p_market_code VARCHAR
        )
        RETURNS TABLE (
            metric_code         VARCHAR,
            default_value       DECIMAL,
            benchmark_avg       DECIMAL,
            benchmark_top25     DECIMAL,
            target_value        DECIMAL,
            warning_threshold   DECIMAL,
            critical_threshold  DECIMAL,
            alert_direction     VARCHAR,
            unit_code           VARCHAR,
            scope_type          VARCHAR
        ) AS $$
            SELECT DISTINCT ON (dmv.metric_code)
                dmv.metric_code,
                dmv.default_value,
                dmv.benchmark_avg,
                dmv.benchmark_top25,
                dmv.target_value,
                dmv.warning_threshold,
                dmv.critical_threshold,
                dmv.alert_direction,
                dmv.unit_code,
                dmv.scope_type
            FROM default_metric_values dmv
            WHERE (dmv.scope_type = 'farm'   AND dmv.scope_code = p_farm_code)
               OR (dmv.scope_type = 'region' AND dmv.scope_code = p_region_code)
               OR (dmv.scope_type = 'market' AND dmv.scope_code = p_market_code)
               OR (dmv.scope_type = 'system' AND dmv.scope_code = 'SYSTEM')
            ORDER BY
                dmv.metric_code,
                CASE dmv.scope_type
                    WHEN 'farm'   THEN 1
                    WHEN 'region' THEN 2
                    WHEN 'market' THEN 3
                    WHEN 'system' THEN 4
                    ELSE 5
                END
        $$ LANGUAGE SQL STABLE;

INSERT INTO default_metric_values
            (scope_type, scope_code, metric_code,
             default_value, benchmark_avg, benchmark_top25, target_value, unit_code,
             warning_threshold, critical_threshold, alert_direction)
        VALUES
        -- ���� SYSTEM fallback (global conservative baseline) ������������������������������
        ('system','SYSTEM','FARROWING_RATE', 80.0, 81.0, 88.0, 90.0, '%',
         80.0, 70.0, 'below'),

        -- ���� KR ��������������������������������������������������������������������������������������������������������������������
        ('region','KR','FARROWING_RATE', 83.0, 85.0, 90.0, 92.0, '%',
         85.0, 75.0, 'below'),

        -- ���� US ��������������������������������������������������������������������������������������������������������������������
        ('region','US','PSY',            22.0, 22.0, 26.0, 28.0, 'piglets/sow/year',
         23.0, 19.0, 'below'),
        ('region','US','NPD',            38.0, 44.0, 30.0, 25.0, 'days',
         38.0, 53.0, 'above'),
        ('region','US','FARROWING_RATE', 80.0, 81.0, 87.0, 90.0, '%',
         83.0, 73.0, 'below'),

        -- ���� BR ��������������������������������������������������������������������������������������������������������������������
        ('region','BR','PSY',            19.0, 20.5, 24.0, 26.0, 'piglets/sow/year',
         21.0, 17.0, 'below'),
        ('region','BR','NPD',            42.0, 48.0, 33.0, 27.0, 'days',
         42.0, 58.0, 'above'),
        ('region','BR','FARROWING_RATE', 78.0, 79.0, 85.0, 88.0, '%',
         80.0, 70.0, 'below'),

        -- ���� CN ��������������������������������������������������������������������������������������������������������������������
        ('region','CN','PSY',            17.0, 18.5, 22.0, 24.0, 'piglets/sow/year',
         19.0, 16.0, 'below'),
        ('region','CN','NPD',            45.0, 52.0, 36.0, 30.0, 'days',
         45.0, 62.0, 'above'),
        ('region','CN','FARROWING_RATE', 75.0, 76.0, 83.0, 86.0, '%',
         78.0, 68.0, 'below'),

        -- ���� VN (Southeast Asia representative) ����������������������������������������������������
        ('region','VN','PSY',            16.0, 17.5, 21.0, 23.0, 'piglets/sow/year',
         18.0, 15.0, 'below'),
        ('region','VN','NPD',            45.0, 54.0, 37.0, 31.0, 'days',
         45.0, 62.0, 'above'),
        ('region','VN','FARROWING_RATE', 74.0, 75.0, 82.0, 85.0, '%',
         78.0, 68.0, 'below')

        ON CONFLICT (scope_type, scope_code, metric_code) DO UPDATE
        SET warning_threshold  = EXCLUDED.warning_threshold,
            critical_threshold = EXCLUDED.critical_threshold,
            alert_direction    = EXCLUDED.alert_direction,
            benchmark_avg      = EXCLUDED.benchmark_avg,
            benchmark_top25    = EXCLUDED.benchmark_top25,
            target_value       = EXCLUDED.target_value,
            updated_at         = NOW();

UPDATE default_metric_values
        SET warning_threshold  = CASE metric_code
                WHEN 'PSY' THEN 24.0
                WHEN 'NPD' THEN 35.0
            END,
            critical_threshold = CASE metric_code
                WHEN 'PSY' THEN 20.0
                WHEN 'NPD' THEN 50.0
            END,
            alert_direction    = CASE metric_code
                WHEN 'PSY' THEN 'below'
                WHEN 'NPD' THEN 'above'
            END
        WHERE scope_type = 'region' AND scope_code = 'KR'
          AND metric_code IN ('PSY', 'NPD');

UPDATE default_metric_values
        SET warning_threshold  = CASE metric_code
                WHEN 'PSY' THEN 22.0
                WHEN 'NPD' THEN 40.0
            END,
            critical_threshold = CASE metric_code
                WHEN 'PSY' THEN 18.0
                WHEN 'NPD' THEN 55.0
            END,
            alert_direction    = CASE metric_code
                WHEN 'PSY' THEN 'below'
                WHEN 'NPD' THEN 'above'
            END
        WHERE scope_type = 'system' AND scope_code = 'SYSTEM'
          AND metric_code IN ('PSY', 'NPD');

UPDATE alembic_version SET version_num='e3f9a2b4c8d1' WHERE alembic_version.version_num = 'c7d4e2a1f9b0';

COMMIT;

