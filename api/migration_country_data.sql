-- PigOS: country-specific seed data delta
-- Apply in Supabase SQL Editor after base schema

-- C. SLAUGHTER_WEIGHT per region
INSERT INTO default_metric_values
    (scope_type, scope_code, metric_code, default_value, target_value,
     warning_threshold, critical_threshold, alert_direction, unit_code)
VALUES
    ('region','KR','SLAUGHTER_WEIGHT',110,110,100,90,'below','kg'),
    ('region','US','SLAUGHTER_WEIGHT',130,130,115,100,'below','kg'),
    ('region','CN','SLAUGHTER_WEIGHT',115,115,100,90,'below','kg'),
    ('region','VN','SLAUGHTER_WEIGHT',95,95,80,70,'below','kg'),
    ('region','TH','SLAUGHTER_WEIGHT',95,95,80,70,'below','kg'),
    ('region','PH','SLAUGHTER_WEIGHT',90,90,80,70,'below','kg'),
    ('region','BR','SLAUGHTER_WEIGHT',125,125,110,100,'below','kg'),
    ('region','DE','SLAUGHTER_WEIGHT',120,120,105,95,'below','kg'),
    ('region','DK','SLAUGHTER_WEIGHT',120,120,105,95,'below','kg'),
    ('region','NL','SLAUGHTER_WEIGHT',120,120,105,95,'below','kg'),
    ('system','SYSTEM','SLAUGHTER_WEIGHT',115,115,100,90,'below','kg')
ON CONFLICT (scope_type, scope_code, metric_code) DO UPDATE
    SET default_value=EXCLUDED.default_value,
        target_value=EXCLUDED.target_value,
        warning_threshold=EXCLUDED.warning_threshold,
        critical_threshold=EXCLUDED.critical_threshold;

-- D. COMPLIANCE_PROFILES
INSERT INTO compliance_profiles
    (profile_code, profile_name, requires_traceability, requires_welfare_metrics,
     requires_antibiotic_tracking, requires_env_reporting, min_wean_period)
VALUES
    ('KR_STANDARD','Korea Standard',TRUE,FALSE,TRUE,FALSE,21),
    ('EU_STANDARD','EU Standard',TRUE,TRUE,TRUE,TRUE,28),
    ('US_STANDARD','US Standard',FALSE,FALSE,TRUE,FALSE,17),
    ('SEA_STANDARD','SEA Standard',FALSE,FALSE,FALSE,FALSE,14),
    ('LATAM_STANDARD','LatAm Standard',FALSE,FALSE,FALSE,FALSE,14),
    ('DEFAULT','Global Default',FALSE,FALSE,FALSE,FALSE,14)
ON CONFLICT (profile_code) DO UPDATE
    SET profile_name=EXCLUDED.profile_name,
        requires_traceability=EXCLUDED.requires_traceability,
        requires_antibiotic_tracking=EXCLUDED.requires_antibiotic_tracking,
        min_wean_period=EXCLUDED.min_wean_period;

-- Link region_defaults → compliance_profiles
UPDATE region_defaults SET compliance_profile_code='KR_STANDARD'   WHERE region_code='KR';
UPDATE region_defaults SET compliance_profile_code='US_STANDARD'   WHERE region_code='US';
UPDATE region_defaults SET compliance_profile_code='EU_STANDARD'   WHERE region_code IN ('DE','DK','NL','ES');
UPDATE region_defaults SET compliance_profile_code='SEA_STANDARD'  WHERE region_code IN ('TH','VN','PH');
UPDATE region_defaults SET compliance_profile_code='LATAM_STANDARD' WHERE region_code='BR';

-- Region weight_unit / currency_code
UPDATE region_defaults SET weight_unit='lb', currency_code='USD' WHERE region_code='US';
UPDATE region_defaults SET weight_unit='kg', currency_code='KRW' WHERE region_code='KR';
UPDATE region_defaults SET weight_unit='kg', currency_code='CNY' WHERE region_code='CN';
UPDATE region_defaults SET weight_unit='kg', currency_code='VND' WHERE region_code='VN';
UPDATE region_defaults SET weight_unit='kg', currency_code='THB' WHERE region_code='TH';
UPDATE region_defaults SET weight_unit='kg', currency_code='PHP' WHERE region_code='PH';
UPDATE region_defaults SET weight_unit='kg', currency_code='BRL' WHERE region_code='BR';
UPDATE region_defaults SET weight_unit='kg', currency_code='EUR' WHERE region_code IN ('DE','DK','NL','ES');
