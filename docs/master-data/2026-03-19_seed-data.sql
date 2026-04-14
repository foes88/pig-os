-- ============================================================================
-- PigOS — Master / Seed Data v1.0
-- ============================================================================
-- 애플리케이션 기동 전 반드시 적재해야 하는 초기 데이터
-- 실행 순서: db-schema-v1.sql → seed-data.sql
-- 2026.03.19
-- ============================================================================


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  1. EVENT DEFINITIONS — 48종 이벤트 타입                                  │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE IF NOT EXISTS event_definitions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_code      VARCHAR(30) UNIQUE NOT NULL,
    category        VARCHAR(20) NOT NULL,
    label_en        VARCHAR(100) NOT NULL,
    label_ko        VARCHAR(100),
    label_vi        VARCHAR(100),
    required_fields JSONB,
    regional_applicability VARCHAR(50) DEFAULT 'ALL',
    phase           VARCHAR(10) DEFAULT 'MVP',
    sort_order      INT
);

INSERT INTO event_definitions (event_code, category, label_en, label_ko, label_vi, required_fields, regional_applicability, phase, sort_order) VALUES
-- REPRODUCTION (14)
('HEAT_DETECTION',    'REPRODUCTION', 'Heat/Estrus Detection',  '발정 감지',      'Phát hiện động dục',   '{"sow_id":"required"}', 'ALL', 'MVP', 1),
('MATING_AI',         'REPRODUCTION', 'Artificial Insemination', 'AI 교배',        'Phối giống nhân tạo',  '{"sow_id":"required","mating_date":"required","semen_batch":"optional"}', 'ALL', 'MVP', 2),
('MATING_NATURAL',    'REPRODUCTION', 'Natural Mating',          '자연 교배',      'Phối giống tự nhiên',  '{"sow_id":"required","boar_id":"required","mating_date":"required"}', 'ALL', 'MVP', 3),
('PREGNANCY_POS',     'REPRODUCTION', 'Pregnancy Check +',       '임신확인 양성',  'Kiểm tra mang thai +', '{"sow_id":"required","check_date":"required","method":"required"}', 'ALL', 'MVP', 4),
('PREGNANCY_NEG',     'REPRODUCTION', 'Pregnancy Check -',       '임신확인 음성',  'Kiểm tra mang thai -', '{"sow_id":"required","check_date":"required"}', 'ALL', 'MVP', 5),
('PREGNANCY_UNCERTAIN','REPRODUCTION','Pregnancy Uncertain',     '임신확인 불확실','Không chắc chắn',      '{"sow_id":"required"}', 'ALL', 'MVP', 6),
('FARROWING_NORMAL',  'REPRODUCTION', 'Normal Farrowing',        '정상 분만',      'Đẻ bình thường',       '{"sow_id":"required","total_born":"required","born_alive":"required"}', 'ALL', 'MVP', 7),
('FARROWING_ASSISTED','REPRODUCTION', 'Assisted Farrowing',      '보조 분만',      'Đẻ hỗ trợ',           '{"sow_id":"required","total_born":"required","born_alive":"required"}', 'ALL', 'MVP', 8),
('ABORTION',          'REPRODUCTION', 'Abortion',                '유산',           'Sẩy thai',             '{"sow_id":"required","date":"required"}', 'ALL', 'MVP', 9),
('RETURN_TO_ESTRUS',  'REPRODUCTION', 'Return to Estrus',        '재발정',         'Quay lại động dục',    '{"sow_id":"required"}', 'ALL', 'MVP', 10),
('WEANING',           'REPRODUCTION', 'Weaning',                 '이유',           'Cai sữa',              '{"sow_id":"required","weaned_count":"required","weaning_date":"required"}', 'ALL', 'MVP', 11),
('FOSTERING_IN',      'REPRODUCTION', 'Cross-fostering In',      '위탁 수입',      'Nhận nuôi',            '{"sow_id":"required","count":"required"}', 'ALL', 'MVP', 12),
('FOSTERING_OUT',     'REPRODUCTION', 'Cross-fostering Out',     '위탁 송출',      'Chuyển nuôi',          '{"sow_id":"required","count":"required"}', 'ALL', 'MVP', 13),
('GILT_SELECTION',    'REPRODUCTION', 'Gilt Selection',           '후보돈 선발',    'Chọn hậu bị',         '{"sow_id":"required","selection_date":"required"}', 'ALL', 'PHASE2', 14),

-- HEALTH (11)
('DISEASE_DIAGNOSIS', 'HEALTH', 'Disease Diagnosis',       '질병 진단',     'Chẩn đoán bệnh',     '{"disease_code":"required","severity":"required"}', 'ALL', 'MVP', 15),
('VACCINATION',       'HEALTH', 'Vaccination',              '백신 접종',     'Tiêm phòng',          '{"vaccine_name":"required","date":"required"}', 'ALL', 'MVP', 16),
('MEDICATION',        'HEALTH', 'Medication',               '투약',          'Cho thuốc',           '{"drug_name":"required","dose_mg":"required"}', 'ALL', 'MVP', 17),
('TREATMENT_START',   'HEALTH', 'Treatment Start',          '치료 시작',     'Bắt đầu điều trị',   '{"sow_id":"required","drug_name":"required"}', 'ALL', 'MVP', 18),
('TREATMENT_END',     'HEALTH', 'Treatment End',            '치료 종료',     'Kết thúc điều trị',   '{"sow_id":"required"}', 'ALL', 'MVP', 19),
('LAMENESS_DETECTED', 'HEALTH', 'Lameness Detected',        '파행 감지',     'Phát hiện khập khiễng','{"sow_id":"required","severity":"required"}', 'ALL', 'MVP', 20),
('PROLAPSE_POP',      'HEALTH', 'Prolapse (POP)',           '골반장기탈출',  'Sa cơ quan',          '{"sow_id":"required"}', 'US', 'MVP', 21),
('INJURY',            'HEALTH', 'Injury',                   '부상',          'Chấn thương',         '{"sow_id":"required"}', 'ALL', 'MVP', 22),
('MORTALITY_SOW',     'HEALTH', 'Sow Mortality',            '모돈 폐사',     'Nái chết',            '{"sow_id":"required","cause":"required"}', 'ALL', 'MVP', 23),
('MORTALITY_PIGLET',  'HEALTH', 'Piglet Mortality',         '자돈 폐사',     'Heo con chết',        '{"count":"required","cause":"optional"}', 'ALL', 'MVP', 24),
('CULLING',           'HEALTH', 'Culling',                  '도태',          'Loại thải',           '{"sow_id":"required","reason":"required"}', 'ALL', 'MVP', 25),

-- FEED (4)
('FEED_DELIVERY',     'FEED', 'Feed Delivery',         '사료 입고',      'Nhập thức ăn',    '{"quantity_kg":"required","feed_type":"required"}', 'ALL', 'PHASE2', 26),
('FEED_BIN_REFILL',   'FEED', 'Feed Bin Refill',       '사료빈 충전',    'Nạp silo',        '{"bin_id":"required","quantity_kg":"required"}', 'ALL', 'PHASE2', 27),
('FEED_FORMULA_CHANGE','FEED','Feed Formula Change',   '배합 변경',      'Đổi công thức',   '{"formula_id":"required"}', 'ALL', 'PHASE2', 28),
('ESF_READING',       'FEED', 'ESF Station Reading',   'ESF 급이 기록',  'Đọc ESF',         '{"station_id":"required","quantity_kg":"required"}', 'ALL', 'PHASE2', 29),

-- MOVEMENT (6)
('TRANSFER_IN',       'MOVEMENT', 'Transfer In',         '전입',        'Nhập trại',       '{"origin":"required","count":"required"}', 'ALL', 'MVP', 30),
('TRANSFER_OUT',      'MOVEMENT', 'Transfer Out',        '전출',        'Xuất trại',       '{"destination":"required","count":"required"}', 'ALL', 'MVP', 31),
('QUARANTINE_IN',     'MOVEMENT', 'Quarantine Start',    '격리 시작',   'Bắt đầu cách ly', '{"reason":"required"}', 'ALL', 'MVP', 32),
('QUARANTINE_OUT',    'MOVEMENT', 'Quarantine End',      '격리 해제',   'Kết thúc cách ly', '{}', 'ALL', 'MVP', 33),
('SHIPMENT_MARKET',   'MOVEMENT', 'Shipment to Market',  '출하',        'Xuất bán',        '{"count":"required","destination":"required"}', 'ALL', 'MVP', 34),
('EXPORT_SHIPMENT',   'MOVEMENT', 'Export Shipment',     '수출 출하',   'Xuất khẩu',       '{"count":"required","ractopamine_free":"required"}', 'BR,US', 'PHASE2', 35),

-- BIOSECURITY (7)
('VISITOR_LOG',       'BIOSECURITY', 'Visitor Log',          '방문자 기록',  'Ghi nhận khách',   '{"visitor_name":"required"}', 'ALL', 'PHASE2', 36),
('EQUIPMENT_DISINFECT','BIOSECURITY','Equipment Disinfection','장비 소독',   'Khử trùng TB',    '{}', 'ALL', 'PHASE2', 37),
('MANURE_DISPOSAL',   'BIOSECURITY', 'Manure Disposal',      '분뇨 처리',   'Xử lý phân',      '{}', 'ALL', 'PHASE3', 38),
('VEHICLE_WASH',      'BIOSECURITY', 'Vehicle Wash',         '차량 세척',   'Rửa xe',           '{}', 'ALL', 'PHASE2', 39),
('ASF_SUSPECTED',     'BIOSECURITY', 'ASF Suspected',        'ASF 의심',    'Nghi ngờ ASF',     '{"affected_count":"required"}', 'SEA,KR,CN', 'MVP', 40),
('ASF_CONFIRMED',     'BIOSECURITY', 'ASF Confirmed',        'ASF 확진',    'Xác nhận ASF',     '{"lab_result":"required"}', 'SEA,KR,CN', 'MVP', 41),
('ASF_VACCINATION',   'BIOSECURITY', 'ASF Vaccination',      'ASF 백신접종','Tiêm vaccine ASF', '{"vaccine_name":"required","batch_no":"required"}', 'SEA', 'MVP', 42),

-- PRODUCTION (4)
('CARCASS_DATA',      'PRODUCTION', 'Carcass Data Received', '도체 데이터 수신','Nhận DL thân thịt', '{"grade":"required","weight":"required"}', 'ALL', 'PHASE2', 43),
('WEIGHT_RECORDING',  'PRODUCTION', 'Weight Recording',      '체중 측정',       'Ghi nhận trọng lượng','{"weight_kg":"required"}', 'ALL', 'MVP', 44),
('BODY_CONDITION',    'PRODUCTION', 'Body Condition Score',   'BCS 점수',        'Điểm thể trạng',   '{"score":"required"}', 'ALL', 'PHASE2', 45),
('BACKFAT_MEASURE',   'PRODUCTION', 'Backfat Measurement',    '등지방 측정',     'Đo mỡ lưng',       '{"mm":"required"}', 'ALL', 'PHASE2', 46),

-- FACILITY (2)
('STALL_TO_GROUP',    'FACILITY', 'Stall to Group Conversion','군사 전환',   'Chuyển chuồng nhóm','{"building_id":"required"}', 'KR,EU', 'PHASE2', 47),
('ENV_ALERT',         'FACILITY', 'Environmental Alert',      '환경 경보',   'Cảnh báo môi trường','{"type":"required","value":"required"}', 'ALL', 'PHASE2', 48);


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  2. DISEASE CODES — 30종 질병 마스터                                      │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE IF NOT EXISTS disease_codes (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    disease_code        VARCHAR(20) UNIQUE NOT NULL,
    woah_code           VARCHAR(20),
    label_en            VARCHAR(100) NOT NULL,
    label_ko            VARCHAR(100),
    label_vi            VARCHAR(100),
    category            VARCHAR(20) NOT NULL,
    notifiable          BOOLEAN DEFAULT FALSE,
    regional_prevalence JSONB,
    typical_mortality_pct DECIMAL(5,2),
    typical_treatment   VARCHAR(200)
);

INSERT INTO disease_codes (disease_code, woah_code, label_en, label_ko, label_vi, category, notifiable, regional_prevalence, typical_mortality_pct, typical_treatment) VALUES
('ASF',         'A010',  'African Swine Fever',           '아프리카돼지열병',  'Dịch tả lợn Châu Phi',     'VIRAL',     TRUE,  '{"KR":"WILDLIFE","US":"FREE","BR":"FREE","DK":"FREE","SEA":"ENDEMIC","CN":"ENDEMIC"}', 100.0, 'Culling + Biosecurity'),
('PRRS_1',      'A0104', 'PRRS Type 1 (EU)',              'PRRS 타입1',       'PRRS loại 1',              'VIRAL',     FALSE, '{"KR":"ENDEMIC","EU":"MANAGED","US":"RARE"}', 15.0, 'Vaccination + Management'),
('PRRS_2',      'A0104', 'PRRS Type 2 (NA)',              'PRRS 타입2',       'PRRS loại 2',              'VIRAL',     FALSE, '{"KR":"ENDEMIC","US":"ENDEMIC","CN":"ENDEMIC","SEA":"ENDEMIC"}', 20.0, 'Vaccination + Management'),
('PRRS_144C',   'A0104', 'PRRS 1-4-4C Lineage',           'PRRS 1-4-4C',     'PRRS 1-4-4C',              'VIRAL',     FALSE, '{"US":"DOMINANT"}', 25.0, 'Vaccination + Air filtration'),
('PRRS_1C5',    'A0104', 'PRRS 1C.5 Lineage',             'PRRS 1C.5',       'PRRS 1C.5',                'VIRAL',     FALSE, '{"US":"EMERGING_2024"}', 20.0, 'Monitoring'),
('FMD',         'A020',  'Foot and Mouth Disease',         '구제역',           'Lở mồm long móng',        'VIRAL',     TRUE,  '{"KR":"VACCINATED","US":"FREE","BR":"FREE","EU":"FREE"}', 5.0, 'Vaccination (KR mandatory)'),
('PED',         NULL,    'Porcine Epidemic Diarrhea',      '돼지유행성설사',   'Tiêu chảy dịch heo',       'VIRAL',     FALSE, '{"US":"SEASONAL","CN":"ENDEMIC","BR":"RARE"}', 80.0, 'Management (piglet)'),
('PCV2',        NULL,    'Porcine Circovirus Type 2',      '돼지써코바이러스', 'Circovirus lợn',            'VIRAL',     FALSE, '{"ALL":"ENDEMIC"}', 10.0, 'Vaccination'),
('APP',         NULL,    'Actinobacillus pleuropneumoniae','흉막폐렴',         'Viêm phổi màng phổi',      'BACTERIAL', FALSE, '{"ALL":"ENDEMIC"}', 15.0, 'Antibiotics (7-14 days)'),
('MMA',         NULL,    'Mastitis-Metritis-Agalactia',    'MMA증후군',        'Hội chứng MMA',            'BACTERIAL', FALSE, '{"ALL":"COMMON"}', 2.0, 'Antibiotics + Oxytocin'),
('PMWS',        NULL,    'Post-weaning Multisystemic',     'PMWS',             'PMWS',                      'VIRAL',     FALSE, '{"ALL":"MANAGED"}', 10.0, 'Vaccination (PCV2)'),
('ILEITIS',     NULL,    'Ileitis (Lawsonia)',             '회장염',           'Viêm hồi tràng',           'BACTERIAL', FALSE, '{"ALL":"ENDEMIC"}', 5.0, 'Antibiotics'),
('ERYSIPELAS',  NULL,    'Swine Erysipelas',               '돼지단독',         'Bệnh đóng dấu',            'BACTERIAL', FALSE, '{"ALL":"ENDEMIC"}', 5.0, 'Penicillin'),
('DYSENTERY',   NULL,    'Swine Dysentery',                '돼지이질',         'Lỵ lợn',                   'BACTERIAL', FALSE, '{"EU":"MANAGED","US":"ENDEMIC"}', 3.0, 'Tiamulin/Lincomycin'),
('GLASSERS',    NULL,    'Glässer Disease',                '글래서병',         'Bệnh Glässer',             'BACTERIAL', FALSE, '{"ALL":"COMMON"}', 20.0, 'Antibiotics'),
('STREP_SUIS',  NULL,    'Streptococcus suis',             '연쇄상구균',       'Liên cầu khuẩn',           'BACTERIAL', FALSE, '{"ALL":"ENDEMIC"}', 15.0, 'Penicillin/Ampicillin'),
('SALMONELLA',  NULL,    'Salmonellosis',                  '살모넬라',         'Salmonella',                'BACTERIAL', FALSE, '{"ALL":"ENDEMIC"}', 3.0, 'Antibiotics + Management'),
('E_COLI',      NULL,    'E. coli (Colibacillosis)',       '대장균',           'E. coli',                  'BACTERIAL', FALSE, '{"ALL":"ENDEMIC"}', 10.0, 'Antibiotics'),
('CLOSTRIDIUM', NULL,    'Clostridial Disease',            '클로스트리디움',   'Clostridium',               'BACTERIAL', FALSE, '{"ALL":"SPORADIC"}', 30.0, 'Vaccination'),
('AUJESZKY',    NULL,    'Aujeszky Disease (PRV)',         '오제스키병',       'Bệnh Aujeszky',            'VIRAL',     TRUE,  '{"US":"ERADICATED","EU":"ERADICATED","CN":"ENDEMIC"}', 80.0, 'Vaccination'),
('SIV',         NULL,    'Swine Influenza',                '돼지인플루엔자',   'Cúm lợn',                  'VIRAL',     FALSE, '{"ALL":"SEASONAL"}', 2.0, 'Supportive care'),
('MYCO',        NULL,    'Mycoplasma hyopneumoniae',       '마이코플라즈마',   'Viêm phổi suyễn',          'BACTERIAL', FALSE, '{"ALL":"ENDEMIC"}', 3.0, 'Vaccination + Antibiotics'),
('LEPTO',       NULL,    'Leptospirosis',                  '렙토스피라',       'Xoắn khuẩn',               'BACTERIAL', FALSE, '{"ALL":"ENDEMIC"}', 5.0, 'Antibiotics'),
('PARVO',       NULL,    'Porcine Parvovirus',             '돼지파보바이러스', 'Parvovirus lợn',            'VIRAL',     FALSE, '{"ALL":"MANAGED"}', 0.0, 'Vaccination (gilt)'),
('TGE',         NULL,    'Transmissible Gastroenteritis',  'TGE',              'Viêm dạ dày ruột',         'VIRAL',     FALSE, '{"US":"SPORADIC","CN":"ENDEMIC"}', 90.0, 'Supportive (piglet)'),
('ROTAVIRUS',   NULL,    'Rotavirus',                      '로타바이러스',     'Rotavirus',                 'VIRAL',     FALSE, '{"ALL":"COMMON"}', 10.0, 'Supportive'),
('COCCIDIA',    NULL,    'Coccidiosis',                    '콕시듐증',         'Cầu trùng',                'PARASITIC', FALSE, '{"ALL":"COMMON"}', 2.0, 'Toltrazuril'),
('MANGE',       NULL,    'Sarcoptic Mange',                '옴',               'Ghẻ',                      'PARASITIC', FALSE, '{"ALL":"COMMON"}', 0.0, 'Ivermectin'),
('LAMENESS',    NULL,    'Lameness (General)',              '파행',             'Khập khiễng',              'MECHANICAL',FALSE, '{"ALL":"COMMON"}', 0.0, 'NSAIDs + Management'),
('HEAT_STRESS', NULL,    'Heat Stress',                    '열사병',           'Sốc nhiệt',               'METABOLIC', FALSE, '{"SEA":"HIGH","CN":"HIGH","KR":"SEASONAL"}', 5.0, 'Cooling + Water');


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  3. VACCINE CATALOG — 25종 백신                                           │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE IF NOT EXISTS vaccine_catalog (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vaccine_code      VARCHAR(30) UNIQUE NOT NULL,
    disease_target    VARCHAR(20),
    vaccine_type      VARCHAR(20),
    product_name      VARCHAR(100),
    manufacturer      VARCHAR(100),
    approved_regions  TEXT[],
    route             VARCHAR(20),
    withdrawal_days   INT DEFAULT 0,
    notes             TEXT
);

INSERT INTO vaccine_catalog (vaccine_code, disease_target, vaccine_type, product_name, manufacturer, approved_regions, route, withdrawal_days, notes) VALUES
-- PRRS
('PRRS_INGELVAC_MLV', 'PRRS_2',  'LIVE',    'Ingelvac PRRS MLV',       'Boehringer Ingelheim', '{US,KR,SEA,CN}', 'IM', 0, 'North American strain'),
('PRRS_FOSTERA',      'PRRS_2',  'LIVE',    'Fostera PRRS',            'Zoetis',               '{US,KR,CN}',     'IM', 0, 'Broad cross-protection'),
('PRRS_PORCILIS',     'PRRS_1',  'LIVE',    'Porcilis PRRS',           'MSD',                  '{EU,KR}',        'IM', 0, 'EU Type 1 strain'),
('PRRS_PREVACENT',    'PRRS_2',  'KILLED',  'Prevacent PRRS',          'Elanco',               '{US}',           'IM', 0, 'Killed virus'),
-- FMD
('FMD_AFTOPOR',       'FMD',     'KILLED',  'AFTOPOR Plus',            'Merial/BI',            '{KR,BR}',        'IM', 21, 'Trivalent O/A/Asia1'),
('FMD_DECIVAC',       'FMD',     'KILLED',  'Decivac FMD DOE',        'MSD',                  '{KR}',           'IM', 21, NULL),
-- ASF (Vietnam only)
('ASF_NAVET',         'ASF',     'LIVE',    'NAVET-ASFVAC',           'NAVET Vietnam',         '{VN}',           'IM', 0, 'Live attenuated, 1st approved globally'),
('ASF_AVAC',          'ASF',     'LIVE',    'AVAC ASF LIVE',          'AVAC Vietnam',          '{VN}',           'IM', 0, 'Gene-deleted live'),
('ASF_DACOVAC',       'ASF',     'SUBUNIT', 'DACOVAC-ASF2',           'Dabaco/VNUA',           '{VN}',           'IM', 0, 'Recombinant P30'),
-- PCV2
('PCV2_CIRCUMVENT',   'PCV2',    'SUBUNIT', 'Circumvent PCV',         'MSD',                  '{ALL}',          'IM', 0, NULL),
('PCV2_CIRCOFLEX',    'PCV2',    'SUBUNIT', 'Ingelvac CircoFLEX',     'Boehringer Ingelheim', '{ALL}',          'IM', 0, NULL),
('PCV2_PORCILIS',     'PCV2',    'SUBUNIT', 'Porcilis PCV',           'MSD',                  '{ALL}',          'IM', 0, NULL),
('PCV2_FOSTERA',      'PCV2',    'SUBUNIT', 'Fostera Gold PCV',       'Zoetis',               '{ALL}',          'IM', 0, NULL),
-- Others
('APP_PORCILIS',      'APP',     'SUBUNIT', 'Porcilis APP',           'MSD',                  '{ALL}',          'IM', 0, NULL),
('ERY_ERYSENG',       'ERYSIPELAS','KILLED','Eryseng Parvo',          'HIPRA',                '{ALL}',          'IM', 21, 'Combo erysipelas+parvo'),
('PARVO_REPROCYC',    'PARVO',   'KILLED',  'ReproCyc ParvoFLEX',    'Boehringer Ingelheim', '{ALL}',          'IM', 0, 'Gilt vaccination'),
('ECOLI_COLIPROTEC',  'E_COLI',  'LIVE',    'Coliprotec F4/F18',     'Elanco',               '{EU,US}',        'ORAL', 0, 'Oral live'),
('CLOST_COVEXIN',     'CLOSTRIDIUM','TOXOID','Covexin 10',            'MSD',                  '{ALL}',          'SC', 21, NULL),
('MYCO_RESPISURE',    'MYCO',    'KILLED',  'Respisure ONE',         'Zoetis',               '{ALL}',          'IM', 0, 'Single dose'),
('SIV_FLUSURE',       'SIV',     'KILLED',  'FluSure XP',            'Zoetis',               '{US,KR}',        'IM', 0, 'Trivalent'),
('PED_HARRISVACCINE', 'PED',     'KILLED',  'iPED+',                 'Harrisvaccines',        '{US}',           'IM', 0, 'RNA particle'),
('LEPTO_PORCILIS',    'LEPTO',   'KILLED',  'Porcilis Leptospira',   'MSD',                  '{ALL}',          'IM', 0, NULL);


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  4. MEDICATION CATALOG — 22종 항생제/약품 + DDDA값                        │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE IF NOT EXISTS medication_catalog (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    active_substance     VARCHAR(100) NOT NULL,
    atcvet_code          VARCHAR(10),
    antibiotic_class     VARCHAR(50),
    ddda_mg_per_kg       DECIMAL(10,4),
    standard_dose_mg_kg  DECIMAL(10,4),
    withdrawal_days_meat INT,
    route                VARCHAR(20),
    vfd_required_us      BOOLEAN DEFAULT FALSE,
    eu_restricted        BOOLEAN DEFAULT FALSE,
    notes                TEXT
);

INSERT INTO medication_catalog (active_substance, atcvet_code, antibiotic_class, ddda_mg_per_kg, standard_dose_mg_kg, withdrawal_days_meat, route, vfd_required_us, eu_restricted, notes) VALUES
('Amoxicillin',           'QJ01CA04', 'PENICILLIN',      25.0,  15.0, 7,  'ORAL',  TRUE,  FALSE, 'Most commonly used'),
('Doxycycline',           'QJ01AA02', 'TETRACYCLINE',    10.0,  10.0, 7,  'ORAL',  TRUE,  FALSE, NULL),
('Oxytetracycline',       'QJ01AA06', 'TETRACYCLINE',    20.0,  20.0, 14, 'IM',    TRUE,  FALSE, 'Long-acting injectable'),
('Tilmicosin',            'QJ01FA91', 'MACROLIDE',       16.0,  16.0, 14, 'ORAL',  TRUE,  FALSE, NULL),
('Tiamulin',              'QJ01XA92', 'PLEUROMUTILIN',   8.8,   8.0,  7,  'ORAL',  TRUE,  FALSE, 'Dysentery treatment'),
('Tylosin',               'QJ01FA90', 'MACROLIDE',       10.0,  10.0, 7,  'ORAL',  TRUE,  FALSE, NULL),
('Lincomycin',            'QJ01FF02', 'LINCOSAMIDE',     22.0,  22.0, 7,  'ORAL',  TRUE,  FALSE, NULL),
('Enrofloxacin',          'QJ01MA90', 'FLUOROQUINOLONE', 5.0,   5.0,  10, 'ORAL',  TRUE,  TRUE,  'EU: Critically important'),
('Ceftiofur',             'QJ01DD90', 'CEPHALOSPORIN',   3.0,   3.0,  14, 'IM',    TRUE,  TRUE,  'EU: Critically important, last resort'),
('Tulathromycin',         'QJ01FA94', 'MACROLIDE',       2.5,   2.5,  14, 'IM',    TRUE,  FALSE, 'Long-acting injectable'),
('Florfenicol',           'QJ01BA90', 'AMPHENICOL',      20.0,  20.0, 18, 'IM',    TRUE,  FALSE, NULL),
('Colistin',              'QA07AA10', 'POLYMYXIN',       3.0,   3.0,  1,  'ORAL',  FALSE, TRUE,  'EU: Severely restricted. Last resort.'),
('Apramycin',             'QA07AA92', 'AMINOGLYCOSIDE',  20.0,  20.0, 28, 'ORAL',  TRUE,  FALSE, 'US orphan drug'),
('Penicillin G',          'QJ01CE01', 'PENICILLIN',      15.0,  15.0, 7,  'IM',    FALSE, FALSE, 'Injectable'),
('Spectinomycin',         'QJ01XX04', 'AMINOCYCLITOL',   10.0,  10.0, 14, 'IM',    TRUE,  FALSE, NULL),
('Gentamicin',            'QJ01GB03', 'AMINOGLYCOSIDE',  4.0,   4.0,  14, 'IM',    TRUE,  TRUE,  'EU: Critically important'),
('Trimethoprim-Sulfa',    'QJ01EW11', 'SULFONAMIDE',     25.0,  25.0, 10, 'ORAL',  TRUE,  FALSE, 'Combination'),
('Flunixin meglumine',    'QM01AG90', 'NSAID',           NULL,  2.2,  12, 'IM',    FALSE, FALSE, 'Anti-inflammatory, not antibiotic'),
('Meloxicam',             'QM01AC06', 'NSAID',           NULL,  0.4,  5,  'IM',    FALSE, FALSE, 'Anti-inflammatory, not antibiotic'),
('Zinc Oxide',            'QA07XA91', NULL,              NULL,  NULL, 0,  'ORAL',  FALSE, TRUE,  'EU: BANNED since 2022 (therapeutic dose)'),
('Toltrazuril',           'QP51AJ01', 'ANTIPROTOZOAL',   NULL,  20.0, 77, 'ORAL',  FALSE, FALSE, 'Coccidiosis treatment'),
('Ivermectin',            'QP54AA01', 'ANTIPARASITIC',   NULL,  0.3,  28, 'SC',    FALSE, FALSE, 'Mange/parasites');


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  5. BENCHMARK BASELINES — 6개 권역 + 7개 프로파일                         │
-- └──────────────────────────────────────────────────────────────────────────┘

INSERT INTO benchmarks (country, region, period, farm_scale, psy_avg, psy_top10, psy_bottom10, fcr_avg, fcr_top10, npd_avg, farrowing_rate_avg, sow_mortality_avg, production_cost_per_kg, cost_currency, source) VALUES
('KR', NULL,  '2023', 'COMMERCIAL', 21.9, 32.5, 20.8, 3.26, 2.60, 40, 82.0, 10.0, NULL,  'KRW', 'HANDON_FARMS 2023'),
('KR', NULL,  '2023', 'TOP_10PCT',  32.5, NULL, NULL, 2.60, NULL, 30, 88.0, 6.0,  NULL,  'KRW', 'HANDON_FARMS 2023'),
('DK', NULL,  '2024', 'COMMERCIAL', 35.6, 36.2, NULL, 2.38, 2.23, 35, 88.0, 8.0,  1.49,  'USD', 'DANBRED 2024'),
('NL', NULL,  '2023', 'COMMERCIAL', 30.0, NULL, NULL, 2.50, NULL, 38, 85.0, 9.0,  1.60,  'USD', 'INTERPIG 2023'),
('DE', NULL,  '2023', 'COMMERCIAL', 27.5, NULL, NULL, 2.60, NULL, 40, 83.0, 10.0, 1.83,  'USD', 'INTERPIG 2023'),
('US', NULL,  '2023', 'COMMERCIAL', 25.1, 31.7, 19.2, 3.00, 2.50, 45, 78.3, 14.5, 1.42,  'USD', 'PIGCHAMP 2023'),
('US', NULL,  '2023', 'TOP_10PCT',  31.7, NULL, NULL, 2.50, NULL, 35, 90.2, 8.0,  1.20,  'USD', 'PIGCHAMP 2023'),
('BR', NULL,  '2023', 'COMMERCIAL', 30.5, NULL, NULL, 2.50, 2.30, NULL, 87.0, 7.0,  1.13,  'USD', 'EMBRAPA/INTERPIG 2023'),
('VN', NULL,  '2023', 'COMMERCIAL', 22.0, 26.0, NULL, 2.70, 2.40, NULL, 78.0, 12.0, NULL,  'USD', 'ESTIMATED'),
('VN', NULL,  '2023', 'SMALL',      14.0, NULL, 10.0, 4.00, 3.50, NULL, 65.0, 20.0, NULL,  'USD', 'ESTIMATED'),
('TH', NULL,  '2023', 'COMMERCIAL', 24.0, 26.0, NULL, 2.60, 2.40, NULL, 80.0, 10.0, NULL,  'USD', 'CP FOODS'),
('PH', NULL,  '2023', 'COMMERCIAL', 20.0, NULL, NULL, 3.00, NULL, NULL, 75.0, 15.0, NULL,  'USD', 'ESTIMATED'),
('CN', NULL,  '2024', 'COMMERCIAL', 24.0, 28.0, NULL, 2.63, 2.40, NULL, NULL, 12.0, NULL,  'CNY', 'WEPIG 2024');


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  6. UNIT CONVERSION TABLE                                                │
-- └──────────────────────────────────────────────────────────────────────────┘

CREATE TABLE IF NOT EXISTS unit_conversions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_unit   VARCHAR(20) NOT NULL,
    to_unit     VARCHAR(20) NOT NULL,
    factor      DECIMAL(15,8) NOT NULL,
    offset_val  DECIMAL(15,8) DEFAULT 0,
    category    VARCHAR(20) NOT NULL,
    UNIQUE(from_unit, to_unit)
);

INSERT INTO unit_conversions (from_unit, to_unit, factor, offset_val, category) VALUES
-- WEIGHT
('kg',    'lb',    2.20462262, 0, 'WEIGHT'),
('lb',    'kg',    0.45359237, 0, 'WEIGHT'),
('kg',    'g',     1000.0,     0, 'WEIGHT'),
('g',     'kg',    0.001,      0, 'WEIGHT'),
('ton',   'kg',    1000.0,     0, 'WEIGHT'),
('kg',    'ton',   0.001,      0, 'WEIGHT'),
('cwt',   'lb',    100.0,      0, 'WEIGHT'),
('cwt',   'kg',    45.359237,  0, 'WEIGHT'),
('lb',    'cwt',   0.01,       0, 'WEIGHT'),
-- TEMPERATURE (use formula: to = from * factor + offset)
('C',     'F',     1.8,        32, 'TEMPERATURE'),
('F',     'C',     0.55556,    -17.7778, 'TEMPERATURE'),
-- AREA
('m2',    'sqft',  10.7639104, 0, 'AREA'),
('sqft',  'm2',    0.09290304, 0, 'AREA'),
('ha',    'acre',  2.47105381, 0, 'AREA'),
('acre',  'ha',    0.40468564, 0, 'AREA'),
-- VOLUME
('L',     'gal',   0.26417205, 0, 'VOLUME'),
('gal',   'L',     3.78541178, 0, 'VOLUME'),
('m3',    'ft3',   35.3146667, 0, 'VOLUME'),
('ft3',   'm3',    0.02831685, 0, 'VOLUME'),
-- LENGTH
('cm',    'inch',  0.39370079, 0, 'LENGTH'),
('inch',  'cm',    2.54,       0, 'LENGTH'),
('mm',    'inch',  0.03937008, 0, 'LENGTH'),
('inch',  'mm',    25.4,       0, 'LENGTH');


-- ┌──────────────────────────────────────────────────────────────────────────┐
-- │  7. COUNTRY CONFIGS — 이미 db-schema-v1.sql S-7에 정의됨                  │
-- │  여기서는 추가 국가만 INSERT                                              │
-- └──────────────────────────────────────────────────────────────────────────┘

-- (country_configs는 db-schema-v1.sql의 S-7 섹션에서 11개국 INSERT 완료)
-- 추가 국가 필요 시 여기에 추가


-- ============================================================================
-- SEED DATA SUMMARY
-- ============================================================================
-- event_definitions:   48 rows (7 categories)
-- disease_codes:       30 rows (VIRAL/BACTERIAL/PARASITIC/METABOLIC/MECHANICAL)
-- vaccine_catalog:     22 rows (PRRS/FMD/ASF/PCV2/APP/ERY/PARVO/ECOLI/CLOST/MYCO/SIV/PED/LEPTO)
-- medication_catalog:  22 rows (with DDDA/ATCvet/VFD/EU restriction flags)
-- benchmarks:          13 rows (KR/DK/NL/DE/US/BR/VN/TH/PH/CN)
-- unit_conversions:    22 rows (WEIGHT/TEMPERATURE/AREA/VOLUME/LENGTH)
-- ============================================================================
