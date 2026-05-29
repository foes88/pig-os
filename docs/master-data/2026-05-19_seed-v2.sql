-- ============================================================================
-- PigOS — Master Data Seed v2.0 (2026-05-19)
-- ============================================================================
-- 대상 스키마: v2.0 + v2.1
-- 실행 순서: db-schema-v2.sql → db-schema-v2.1.sql → (이 파일)
-- 멱등성: ON CONFLICT DO NOTHING — 중복 실행 안전
-- ============================================================================


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  0. 테이블 생성 (없으면)                                                  │
-- │  Alembic 마이그레이션이 선행되면 이 블록은 무시됨 (IF NOT EXISTS)          │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE IF NOT EXISTS event_definitions (
    event_code              VARCHAR(30)  PRIMARY KEY,
    category                VARCHAR(20)  NOT NULL,
    label_en                VARCHAR(100) NOT NULL,
    label_ko                VARCHAR(100),
    label_vi                VARCHAR(100),
    required_fields         JSONB,
    regional_applicability  VARCHAR(50)  DEFAULT 'ALL',
    phase                   VARCHAR(10)  DEFAULT 'MVP',
    sort_order              INT
);

CREATE TABLE IF NOT EXISTS disease_codes (
    disease_code            VARCHAR(20)  PRIMARY KEY,
    woah_code               VARCHAR(20),
    label_en                VARCHAR(100) NOT NULL,
    label_ko                VARCHAR(100),
    label_vi                VARCHAR(100),
    category                VARCHAR(20)  NOT NULL,
    notifiable              BOOLEAN      DEFAULT FALSE,
    regional_prevalence     JSONB,
    typical_mortality_pct   NUMERIC(5,2),
    typical_treatment       TEXT
);

CREATE TABLE IF NOT EXISTS vaccine_catalog (
    vaccine_code            VARCHAR(30)  PRIMARY KEY,
    disease_target          VARCHAR(20),
    vaccine_type            VARCHAR(20),
    product_name            VARCHAR(100),
    manufacturer            VARCHAR(100),
    approved_regions        TEXT[],
    route                   VARCHAR(20),
    withdrawal_days         INT          DEFAULT 0,
    notes                   TEXT
);

CREATE TABLE IF NOT EXISTS medication_catalog (
    active_substance        VARCHAR(100) PRIMARY KEY,
    atcvet_code             VARCHAR(10),
    antibiotic_class        VARCHAR(50),
    ddda_mg_per_kg          NUMERIC(10,4),
    standard_dose_mg_kg     NUMERIC(10,4),
    withdrawal_days_meat    INT,
    route                   VARCHAR(20),
    vfd_required_us         BOOLEAN      DEFAULT FALSE,
    eu_restricted           BOOLEAN      DEFAULT FALSE,
    notes                   TEXT
);


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  1. EVENT DEFINITIONS — 48종 이벤트 타입                                  │
-- └──────────────────────────────────────────────────────────────────────────┘

INSERT INTO event_definitions (event_code, category, label_en, label_ko, label_vi, required_fields, regional_applicability, phase, sort_order) VALUES
-- REPRODUCTION (14)
('HEAT_DETECTION',     'REPRODUCTION', 'Heat/Estrus Detection',   '발정 감지',     'Phát hiện động dục',    '{"sow_id":"required"}', 'ALL', 'MVP', 1),
('MATING_AI',          'REPRODUCTION', 'Artificial Insemination',  'AI 교배',       'Phối giống nhân tạo',   '{"sow_id":"required","mating_date":"required","semen_batch":"optional"}', 'ALL', 'MVP', 2),
('MATING_NATURAL',     'REPRODUCTION', 'Natural Mating',           '자연 교배',     'Phối giống tự nhiên',   '{"sow_id":"required","boar_id":"required","mating_date":"required"}', 'ALL', 'MVP', 3),
('PREGNANCY_POS',      'REPRODUCTION', 'Pregnancy Check +',        '임신확인 양성', 'Kiểm tra mang thai +',  '{"sow_id":"required","check_date":"required","method":"required"}', 'ALL', 'MVP', 4),
('PREGNANCY_NEG',      'REPRODUCTION', 'Pregnancy Check -',        '임신확인 음성', 'Kiểm tra mang thai -',  '{"sow_id":"required","check_date":"required"}', 'ALL', 'MVP', 5),
('PREGNANCY_UNCERTAIN','REPRODUCTION', 'Pregnancy Uncertain',      '임신확인 불확실','Không chắc chắn',      '{"sow_id":"required"}', 'ALL', 'MVP', 6),
('FARROWING_NORMAL',   'REPRODUCTION', 'Normal Farrowing',         '정상 분만',     'Đẻ bình thường',        '{"sow_id":"required","total_born":"required","born_alive":"required"}', 'ALL', 'MVP', 7),
('FARROWING_ASSISTED', 'REPRODUCTION', 'Assisted Farrowing',       '보조 분만',     'Đẻ hỗ trợ',            '{"sow_id":"required","total_born":"required","born_alive":"required"}', 'ALL', 'MVP', 8),
('ABORTION',           'REPRODUCTION', 'Abortion',                 '유산',          'Sẩy thai',              '{"sow_id":"required","date":"required"}', 'ALL', 'MVP', 9),
('RETURN_TO_ESTRUS',   'REPRODUCTION', 'Return to Estrus',         '재발정',        'Quay lại động dục',     '{"sow_id":"required"}', 'ALL', 'MVP', 10),
('WEANING',            'REPRODUCTION', 'Weaning',                  '이유',          'Cai sữa',               '{"sow_id":"required","weaned_count":"required","weaning_date":"required"}', 'ALL', 'MVP', 11),
('FOSTERING_IN',       'REPRODUCTION', 'Cross-fostering In',       '위탁 수입',     'Nhận nuôi',             '{"sow_id":"required","count":"required"}', 'ALL', 'MVP', 12),
('FOSTERING_OUT',      'REPRODUCTION', 'Cross-fostering Out',      '위탁 송출',     'Chuyển nuôi',           '{"sow_id":"required","count":"required"}', 'ALL', 'MVP', 13),
('GILT_SELECTION',     'REPRODUCTION', 'Gilt Selection',           '후보돈 선발',   'Chọn hậu bị',           '{"sow_id":"required","selection_date":"required"}', 'ALL', 'PHASE2', 14),

-- HEALTH (11)
('DISEASE_DIAGNOSIS',  'HEALTH', 'Disease Diagnosis',        '질병 진단',     'Chẩn đoán bệnh',      '{"disease_code":"required","severity":"required"}', 'ALL', 'MVP', 15),
('VACCINATION',        'HEALTH', 'Vaccination',               '백신 접종',     'Tiêm phòng',           '{"vaccine_code":"required","date":"required"}', 'ALL', 'MVP', 16),
('MEDICATION',         'HEALTH', 'Medication',                '투약',          'Cho thuốc',            '{"active_substance":"required","dose_mg":"required"}', 'ALL', 'MVP', 17),
('TREATMENT_START',    'HEALTH', 'Treatment Start',           '치료 시작',     'Bắt đầu điều trị',    '{"sow_id":"required","active_substance":"required"}', 'ALL', 'MVP', 18),
('TREATMENT_END',      'HEALTH', 'Treatment End',             '치료 종료',     'Kết thúc điều trị',    '{"sow_id":"required"}', 'ALL', 'MVP', 19),
('LAMENESS_DETECTED',  'HEALTH', 'Lameness Detected',         '파행 감지',     'Phát hiện khập khiễng','{"sow_id":"required","severity":"required"}', 'ALL', 'MVP', 20),
('PROLAPSE_POP',       'HEALTH', 'Prolapse (POP)',            '골반장기탈출',  'Sa cơ quan',           '{"sow_id":"required"}', 'US', 'MVP', 21),
('INJURY',             'HEALTH', 'Injury',                    '부상',          'Chấn thương',          '{"sow_id":"required"}', 'ALL', 'MVP', 22),
('MORTALITY_SOW',      'HEALTH', 'Sow Mortality',             '모돈 폐사',     'Nái chết',             '{"sow_id":"required","cause":"required"}', 'ALL', 'MVP', 23),
('MORTALITY_PIGLET',   'HEALTH', 'Piglet Mortality',          '자돈 폐사',     'Heo con chết',         '{"count":"required","cause":"optional"}', 'ALL', 'MVP', 24),
('CULLING',            'HEALTH', 'Culling',                   '도태',          'Loại thải',            '{"sow_id":"required","reason":"required"}', 'ALL', 'MVP', 25),

-- FEED (4)
('FEED_DELIVERY',      'FEED', 'Feed Delivery',          '사료 입고',     'Nhập thức ăn',     '{"quantity_kg":"required","feed_type":"required"}', 'ALL', 'PHASE2', 26),
('FEED_BIN_REFILL',    'FEED', 'Feed Bin Refill',        '사료빈 충전',   'Nạp silo',         '{"bin_id":"required","quantity_kg":"required"}', 'ALL', 'PHASE2', 27),
('FEED_FORMULA_CHANGE','FEED', 'Feed Formula Change',    '배합 변경',     'Đổi công thức',    '{"formula_id":"required"}', 'ALL', 'PHASE2', 28),
('ESF_READING',        'FEED', 'ESF Station Reading',    'ESF 급이 기록', 'Đọc ESF',          '{"station_id":"required","quantity_kg":"required"}', 'ALL', 'PHASE2', 29),

-- MOVEMENT (6)
('TRANSFER_IN',        'MOVEMENT', 'Transfer In',          '전입',        'Nhập trại',        '{"origin":"required","count":"required"}', 'ALL', 'MVP', 30),
('TRANSFER_OUT',       'MOVEMENT', 'Transfer Out',         '전출',        'Xuất trại',        '{"destination":"required","count":"required"}', 'ALL', 'MVP', 31),
('QUARANTINE_IN',      'MOVEMENT', 'Quarantine Start',     '격리 시작',   'Bắt đầu cách ly',  '{"reason":"required"}', 'ALL', 'MVP', 32),
('QUARANTINE_OUT',     'MOVEMENT', 'Quarantine End',       '격리 해제',   'Kết thúc cách ly', '{}', 'ALL', 'MVP', 33),
('SHIPMENT_MARKET',    'MOVEMENT', 'Shipment to Market',   '출하',        'Xuất bán',         '{"count":"required","destination":"required"}', 'ALL', 'MVP', 34),
('EXPORT_SHIPMENT',    'MOVEMENT', 'Export Shipment',      '수출 출하',   'Xuất khẩu',        '{"count":"required","ractopamine_free":"required"}', 'BR,US', 'PHASE2', 35),

-- BIOSECURITY (7)
('VISITOR_LOG',        'BIOSECURITY', 'Visitor Log',           '방문자 기록', 'Ghi nhận khách',    '{"visitor_name":"required"}', 'ALL', 'PHASE2', 36),
('EQUIPMENT_DISINFECT','BIOSECURITY', 'Equipment Disinfection', '장비 소독',  'Khử trùng TB',     '{}', 'ALL', 'PHASE2', 37),
('MANURE_DISPOSAL',    'BIOSECURITY', 'Manure Disposal',        '분뇨 처리',  'Xử lý phân',       '{}', 'ALL', 'PHASE3', 38),
('VEHICLE_WASH',       'BIOSECURITY', 'Vehicle Wash',           '차량 세척',  'Rửa xe',            '{}', 'ALL', 'PHASE2', 39),
('ASF_SUSPECTED',      'BIOSECURITY', 'ASF Suspected',          'ASF 의심',   'Nghi ngờ ASF',     '{"affected_count":"required"}', 'SEA,KR,CN', 'MVP', 40),
('ASF_CONFIRMED',      'BIOSECURITY', 'ASF Confirmed',          'ASF 확진',   'Xác nhận ASF',     '{"lab_result":"required"}', 'SEA,KR,CN', 'MVP', 41),
('ASF_VACCINATION',    'BIOSECURITY', 'ASF Vaccination',        'ASF 백신접종','Tiêm vaccine ASF', '{"vaccine_code":"required","batch_no":"required"}', 'SEA,VN', 'MVP', 42),

-- PRODUCTION (4)
('CARCASS_DATA',       'PRODUCTION', 'Carcass Data Received',  '도체 데이터 수신','Nhận DL thân thịt', '{"grade":"required","weight":"required"}', 'ALL', 'PHASE2', 43),
('WEIGHT_RECORDING',   'PRODUCTION', 'Weight Recording',        '체중 측정',       'Ghi trọng lượng',   '{"weight_kg":"required"}', 'ALL', 'MVP', 44),
('BODY_CONDITION',     'PRODUCTION', 'Body Condition Score',    'BCS 점수',        'Điểm thể trạng',    '{"score":"required"}', 'ALL', 'PHASE2', 45),
('BACKFAT_MEASURE',    'PRODUCTION', 'Backfat Measurement',     '등지방 측정',     'Đo mỡ lưng',        '{"mm":"required"}', 'ALL', 'PHASE2', 46),

-- FACILITY (2)
('STALL_TO_GROUP',     'FACILITY', 'Stall to Group Conversion','군사 전환',   'Chuyển chuồng nhóm','{"building_id":"required"}', 'KR,EU', 'PHASE2', 47),
('ENV_ALERT',          'FACILITY', 'Environmental Alert',       '환경 경보',   'Cảnh báo môi trường','{"type":"required","value":"required"}', 'ALL', 'PHASE2', 48)

ON CONFLICT (event_code) DO NOTHING;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  2. DISEASE CODES — 30종 질병 마스터                                      │
-- └──────────────────────────────────────────────────────────────────────────┘

INSERT INTO disease_codes
    (disease_code, woah_code, label_en, label_ko, label_vi, category, notifiable, regional_prevalence, typical_mortality_pct, typical_treatment)
VALUES
-- VIRAL (16)
('ASF',         'A010',  'African Swine Fever',             '아프리카돼지열병',    'Dịch tả lợn Châu Phi',     'VIRAL',     TRUE,  '{"KR":"WILDLIFE","US":"FREE","BR":"FREE","DK":"FREE","SEA":"ENDEMIC","CN":"ENDEMIC"}', 100.0, 'Culling + Biosecurity'),
('PRRS_1',      'A0104', 'PRRS Type 1 (EU)',                'PRRS 타입1',         'PRRS loại 1',               'VIRAL',     FALSE, '{"KR":"ENDEMIC","EU":"MANAGED","US":"RARE"}', 15.0, 'Vaccination + Management'),
('PRRS_2',      'A0104', 'PRRS Type 2 (NA)',                'PRRS 타입2',         'PRRS loại 2',               'VIRAL',     FALSE, '{"KR":"ENDEMIC","US":"ENDEMIC","CN":"ENDEMIC","SEA":"ENDEMIC"}', 20.0, 'Vaccination + Management'),
('PRRS_144C',   'A0104', 'PRRS 1-4-4C Lineage',             'PRRS 1-4-4C',        'PRRS 1-4-4C',               'VIRAL',     FALSE, '{"US":"DOMINANT"}', 25.0, 'Vaccination + Air filtration'),
('PRRS_1C5',    'A0104', 'PRRS 1C.5 Lineage',               'PRRS 1C.5',          'PRRS 1C.5',                 'VIRAL',     FALSE, '{"US":"EMERGING_2024"}', 20.0, 'Monitoring'),
('FMD',         'A020',  'Foot and Mouth Disease',           '구제역',             'Lở mồm long móng',          'VIRAL',     TRUE,  '{"KR":"VACCINATED","US":"FREE","BR":"FREE","EU":"FREE"}', 5.0, 'Vaccination (KR mandatory)'),
('PED',         NULL,    'Porcine Epidemic Diarrhea',        '돼지유행성설사',     'Tiêu chảy dịch heo',        'VIRAL',     FALSE, '{"US":"SEASONAL","CN":"ENDEMIC","BR":"RARE"}', 80.0, 'Management (piglet)'),
('PCV2',        NULL,    'Porcine Circovirus Type 2',        '돼지써코바이러스',   'Circovirus lợn',             'VIRAL',     FALSE, '{"ALL":"ENDEMIC"}', 10.0, 'Vaccination'),
('PMWS',        NULL,    'Post-weaning Multisystemic',       'PMWS',               'PMWS',                       'VIRAL',     FALSE, '{"ALL":"MANAGED"}', 10.0, 'Vaccination (PCV2)'),
('AUJESZKY',    NULL,    'Aujeszky Disease (PRV)',           '오제스키병',         'Bệnh Aujeszky',             'VIRAL',     TRUE,  '{"US":"ERADICATED","EU":"ERADICATED","CN":"ENDEMIC"}', 80.0, 'Vaccination'),
('SIV',         NULL,    'Swine Influenza',                  '돼지인플루엔자',     'Cúm lợn',                   'VIRAL',     FALSE, '{"ALL":"SEASONAL"}', 2.0, 'Supportive care'),
('PED_DELTA',   NULL,    'PED Delta CoV',                    'PDCoV',              'PDCoV',                      'VIRAL',     FALSE, '{"US":"SPORADIC","CN":"ENDEMIC"}', 40.0, 'Supportive (piglet)'),
('TGE',         NULL,    'Transmissible Gastroenteritis',    'TGE',                'Viêm dạ dày ruột',          'VIRAL',     FALSE, '{"US":"SPORADIC","CN":"ENDEMIC"}', 90.0, 'Supportive (piglet)'),
('ROTAVIRUS',   NULL,    'Rotavirus',                        '로타바이러스',       'Rotavirus',                  'VIRAL',     FALSE, '{"ALL":"COMMON"}', 10.0, 'Supportive'),
('PARVO',       NULL,    'Porcine Parvovirus',               '돼지파보바이러스',   'Parvovirus lợn',             'VIRAL',     FALSE, '{"ALL":"MANAGED"}', 0.0, 'Vaccination (gilt)'),
('LSVD',        NULL,    'Lumpy Skin / Vesicular Disease',   '수포성 구내염',      'Bệnh mụn nước',             'VIRAL',     TRUE,  '{"SEA":"SPORADIC"}', 2.0, 'Biosecurity'),

-- BACTERIAL (10)
('APP',         NULL,    'Actinobacillus pleuropneumoniae',  '흉막폐렴',           'Viêm phổi màng phổi',       'BACTERIAL', FALSE, '{"ALL":"ENDEMIC"}', 15.0, 'Antibiotics (7-14 days)'),
('MMA',         NULL,    'Mastitis-Metritis-Agalactia',      'MMA증후군',          'Hội chứng MMA',             'BACTERIAL', FALSE, '{"ALL":"COMMON"}', 2.0, 'Antibiotics + Oxytocin'),
('ILEITIS',     NULL,    'Ileitis (Lawsonia intracellularis)','회장염',            'Viêm hồi tràng',            'BACTERIAL', FALSE, '{"ALL":"ENDEMIC"}', 5.0, 'Antibiotics'),
('ERYSIPELAS',  NULL,    'Swine Erysipelas',                 '돼지단독',           'Bệnh đóng dấu',             'BACTERIAL', FALSE, '{"ALL":"ENDEMIC"}', 5.0, 'Penicillin'),
('DYSENTERY',   NULL,    'Swine Dysentery (Brachyspira)',    '돼지이질',           'Lỵ lợn',                    'BACTERIAL', FALSE, '{"EU":"MANAGED","US":"ENDEMIC"}', 3.0, 'Tiamulin/Lincomycin'),
('GLASSERS',    NULL,    'Glässer Disease',                  '글래서병',           'Bệnh Glässer',              'BACTERIAL', FALSE, '{"ALL":"COMMON"}', 20.0, 'Antibiotics'),
('STREP_SUIS',  NULL,    'Streptococcus suis',               '연쇄상구균',         'Liên cầu khuẩn',            'BACTERIAL', FALSE, '{"ALL":"ENDEMIC"}', 15.0, 'Penicillin/Ampicillin'),
('SALMONELLA',  NULL,    'Salmonellosis',                    '살모넬라',           'Salmonella',                 'BACTERIAL', FALSE, '{"ALL":"ENDEMIC"}', 3.0, 'Antibiotics + Management'),
('E_COLI',      NULL,    'E. coli (Colibacillosis)',         '대장균',             'E. coli',                   'BACTERIAL', FALSE, '{"ALL":"ENDEMIC"}', 10.0, 'Antibiotics'),
('MYCO',        NULL,    'Mycoplasma hyopneumoniae',         '마이코플라즈마',     'Viêm phổi suyễn',           'BACTERIAL', FALSE, '{"ALL":"ENDEMIC"}', 3.0, 'Vaccination + Antibiotics'),

-- PARASITIC / OTHER (4)
('CLOSTRIDIUM', NULL,    'Clostridial Disease',              '클로스트리디움',     'Clostridium',                'BACTERIAL', FALSE, '{"ALL":"SPORADIC"}', 30.0, 'Vaccination'),
('LEPTO',       NULL,    'Leptospirosis',                    '렙토스피라',         'Xoắn khuẩn',                'BACTERIAL', FALSE, '{"ALL":"ENDEMIC"}', 5.0, 'Antibiotics'),
('COCCIDIA',    NULL,    'Coccidiosis (Isospora suis)',      '콕시듐증',           'Cầu trùng',                 'PARASITIC', FALSE, '{"ALL":"COMMON"}', 2.0, 'Toltrazuril'),
('MANGE',       NULL,    'Sarcoptic Mange',                  '옴',                 'Ghẻ',                        'PARASITIC', FALSE, '{"ALL":"COMMON"}', 0.0, 'Ivermectin'),

-- METABOLIC / MECHANICAL (2)
('LAMENESS',    NULL,    'Lameness (General)',               '파행',               'Khập khiễng',               'MECHANICAL',FALSE, '{"ALL":"COMMON"}', 0.0, 'NSAIDs + Management'),
('HEAT_STRESS', NULL,    'Heat Stress',                      '열사병',             'Sốc nhiệt',                 'METABOLIC', FALSE, '{"SEA":"HIGH","CN":"HIGH","KR":"SEASONAL"}', 5.0, 'Cooling + Water')

ON CONFLICT (disease_code) DO NOTHING;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  3. VACCINE CATALOG — 22종 백신                                           │
-- └──────────────────────────────────────────────────────────────────────────┘

INSERT INTO vaccine_catalog
    (vaccine_code, disease_target, vaccine_type, product_name, manufacturer, approved_regions, route, withdrawal_days, notes)
VALUES
-- PRRS (4)
('PRRS_INGELVAC_MLV', 'PRRS_2',    'LIVE',    'Ingelvac PRRS MLV',        'Boehringer Ingelheim', '{US,KR,SEA,CN}', 'IM', 0, 'North American PRRS-2 strain'),
('PRRS_FOSTERA',      'PRRS_2',    'LIVE',    'Fostera PRRS',             'Zoetis',               '{US,KR,CN}',     'IM', 0, 'Broad cross-protection'),
('PRRS_PORCILIS',     'PRRS_1',    'LIVE',    'Porcilis PRRS',            'MSD',                  '{EU,KR}',        'IM', 0, 'EU Type 1 strain'),
('PRRS_PREVACENT',    'PRRS_2',    'KILLED',  'Prevacent PRRS',           'Elanco',               '{US}',           'IM', 0, 'Killed virus'),
-- FMD (2)
('FMD_AFTOPOR',       'FMD',       'KILLED',  'AFTOPOR Plus',             'Merial/BI',            '{KR,BR}',        'IM', 21, 'Trivalent O/A/Asia1'),
('FMD_DECIVAC',       'FMD',       'KILLED',  'Decivac FMD DOE',          'MSD',                  '{KR}',           'IM', 21, NULL),
-- ASF — Vietnam-approved (3)
('ASF_NAVET',         'ASF',       'LIVE',    'NAVET-ASFVAC',             'NAVET Vietnam',        '{VN}',           'IM', 0, 'First globally approved live attenuated ASF vaccine'),
('ASF_AVAC',          'ASF',       'LIVE',    'AVAC ASF LIVE',            'AVAC Vietnam',         '{VN}',           'IM', 0, 'Gene-deleted live'),
('ASF_DACOVAC',       'ASF',       'SUBUNIT', 'DACOVAC-ASF2',             'Dabaco/VNUA',          '{VN}',           'IM', 0, 'Recombinant P30 subunit'),
-- PCV2 (4)
('PCV2_CIRCUMVENT',   'PCV2',      'SUBUNIT', 'Circumvent PCV',           'MSD',                  '{ALL}',          'IM', 0, NULL),
('PCV2_CIRCOFLEX',    'PCV2',      'SUBUNIT', 'Ingelvac CircoFLEX',       'Boehringer Ingelheim', '{ALL}',          'IM', 0, NULL),
('PCV2_PORCILIS',     'PCV2',      'SUBUNIT', 'Porcilis PCV',             'MSD',                  '{ALL}',          'IM', 0, NULL),
('PCV2_FOSTERA',      'PCV2',      'SUBUNIT', 'Fostera Gold PCV',         'Zoetis',               '{ALL}',          'IM', 0, NULL),
-- Others (9)
('APP_PORCILIS',      'APP',       'SUBUNIT', 'Porcilis APP',             'MSD',                  '{ALL}',          'IM', 0, NULL),
('ERY_ERYSENG',       'ERYSIPELAS','KILLED',  'Eryseng Parvo',            'HIPRA',                '{ALL}',          'IM', 21, 'Combo erysipelas+parvo'),
('PARVO_REPROCYC',    'PARVO',     'KILLED',  'ReproCyc ParvoFLEX',       'Boehringer Ingelheim', '{ALL}',          'IM', 0, 'Gilt vaccination'),
('ECOLI_COLIPROTEC',  'E_COLI',    'LIVE',    'Coliprotec F4/F18',        'Elanco',               '{EU,US}',        'ORAL', 0, 'Oral live'),
('CLOST_COVEXIN',     'CLOSTRIDIUM','TOXOID', 'Covexin 10',               'MSD',                  '{ALL}',          'SC', 21, NULL),
('MYCO_RESPISURE',    'MYCO',      'KILLED',  'Respisure ONE',            'Zoetis',               '{ALL}',          'IM', 0, 'Single dose'),
('SIV_FLUSURE',       'SIV',       'KILLED',  'FluSure XP',               'Zoetis',               '{US,KR}',        'IM', 0, 'Trivalent'),
('PED_HARRISVACCINE', 'PED',       'KILLED',  'iPED+',                    'Harrisvaccines',       '{US}',           'IM', 0, 'RNA particle platform'),
('LEPTO_PORCILIS',    'LEPTO',     'KILLED',  'Porcilis Leptospira',      'MSD',                  '{ALL}',          'IM', 0, NULL)

ON CONFLICT (vaccine_code) DO NOTHING;


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  4. MEDICATION CATALOG — 22종 항생제/약품                                  │
-- │  DDDA = Defined Daily Dose Animal (mg/kg). VFD = US Vet Feed Directive.  │
-- └──────────────────────────────────────────────────────────────────────────┘

INSERT INTO medication_catalog
    (active_substance, atcvet_code, antibiotic_class, ddda_mg_per_kg, standard_dose_mg_kg, withdrawal_days_meat, route, vfd_required_us, eu_restricted, notes)
VALUES
('Amoxicillin',         'QJ01CA04', 'PENICILLIN',      25.0,  15.0, 7,  'ORAL',  TRUE,  FALSE, 'Most widely used broad-spectrum'),
('Doxycycline',         'QJ01AA02', 'TETRACYCLINE',    10.0,  10.0, 7,  'ORAL',  TRUE,  FALSE, NULL),
('Oxytetracycline',     'QJ01AA06', 'TETRACYCLINE',    20.0,  20.0, 14, 'IM',    TRUE,  FALSE, 'Long-acting injectable'),
('Tilmicosin',          'QJ01FA91', 'MACROLIDE',       16.0,  16.0, 14, 'ORAL',  TRUE,  FALSE, NULL),
('Tiamulin',            'QJ01XA92', 'PLEUROMUTILIN',   8.8,   8.0,  7,  'ORAL',  TRUE,  FALSE, 'Dysentery first-line'),
('Tylosin',             'QJ01FA90', 'MACROLIDE',       10.0,  10.0, 7,  'ORAL',  TRUE,  FALSE, NULL),
('Lincomycin',          'QJ01FF02', 'LINCOSAMIDE',     22.0,  22.0, 7,  'ORAL',  TRUE,  FALSE, NULL),
('Enrofloxacin',        'QJ01MA90', 'FLUOROQUINOLONE', 5.0,   5.0,  10, 'ORAL',  TRUE,  TRUE,  'EU: Critically important antimicrobial'),
('Ceftiofur',           'QJ01DD90', 'CEPHALOSPORIN',   3.0,   3.0,  14, 'IM',    TRUE,  TRUE,  'EU: Last resort. Requires VFD in US.'),
('Tulathromycin',       'QJ01FA94', 'MACROLIDE',       2.5,   2.5,  14, 'IM',    TRUE,  FALSE, 'Long-acting, single injection'),
('Florfenicol',         'QJ01BA90', 'AMPHENICOL',      20.0,  20.0, 18, 'IM',    TRUE,  FALSE, NULL),
('Colistin',            'QA07AA10', 'POLYMYXIN',       3.0,   3.0,  1,  'ORAL',  FALSE, TRUE,  'EU: Severely restricted; last resort only'),
('Apramycin',           'QA07AA92', 'AMINOGLYCOSIDE',  20.0,  20.0, 28, 'ORAL',  TRUE,  FALSE, 'US orphan drug status'),
('Penicillin G',        'QJ01CE01', 'PENICILLIN',      15.0,  15.0, 7,  'IM',    FALSE, FALSE, 'Injectable, no VFD required'),
('Spectinomycin',       'QJ01XX04', 'AMINOCYCLITOL',   10.0,  10.0, 14, 'IM',    TRUE,  FALSE, NULL),
('Gentamicin',          'QJ01GB03', 'AMINOGLYCOSIDE',  4.0,   4.0,  14, 'IM',    TRUE,  TRUE,  'EU: Critically important; renal tox risk'),
('Trimethoprim-Sulfa',  'QJ01EW11', 'SULFONAMIDE',     25.0,  25.0, 10, 'ORAL',  TRUE,  FALSE, 'Combination product'),
('Flunixin meglumine',  'QM01AG90', 'NSAID',           NULL,  2.2,  12, 'IM',    FALSE, FALSE, 'Anti-inflammatory, not antibiotic'),
('Meloxicam',           'QM01AC06', 'NSAID',           NULL,  0.4,  5,  'IM',    FALSE, FALSE, 'Anti-inflammatory, not antibiotic'),
('Zinc Oxide',          'QA07XA91', NULL,              NULL,  NULL, 0,  'ORAL',  FALSE, TRUE,  'EU: BANNED (therapeutic dose) since Jun 2022'),
('Toltrazuril',         'QP51AJ01', 'ANTIPROTOZOAL',   NULL,  20.0, 77, 'ORAL',  FALSE, FALSE, 'Coccidiosis treatment (piglet)'),
('Ivermectin',          'QP54AA01', 'ANTIPARASITIC',   NULL,  0.3,  28, 'SC',    FALSE, FALSE, 'Mange / internal parasites')

ON CONFLICT (active_substance) DO NOTHING;


-- ============================================================================
-- SUMMARY
-- ============================================================================
-- event_definitions:   48 rows (REPRODUCTION 14 / HEALTH 11 / FEED 4 / MOVEMENT 6 / BIOSECURITY 7 / PRODUCTION 4 / FACILITY 2)
-- disease_codes:       32 rows (VIRAL 16 / BACTERIAL 12 / PARASITIC 2 / METABOLIC 1 / MECHANICAL 1)
-- vaccine_catalog:     22 rows
-- medication_catalog:  22 rows (antibiotics + NSAIDs + antiparasitics)
-- ============================================================================
