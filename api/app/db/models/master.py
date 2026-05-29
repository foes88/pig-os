"""
Global reference / master data tables.
No farm_id — these are system-wide catalogs shared across all tenants.

Tables:
  event_definitions   — 48 event types (REPRODUCTION/HEALTH/FEED/…)
  disease_codes       — 30 swine diseases with WOAH codes
  vaccine_catalog     — 22+ vaccines with regional approvals
  medication_catalog  — 22 antibiotics/drugs with DDDA/ATCvet/VFD/EU flags
"""
from sqlalchemy import Boolean, Column, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB

from app.db.base import Base


class EventDefinition(Base):
    __tablename__ = "event_definitions"

    event_code              = Column(String(30),  primary_key=True)
    category                = Column(String(20),  nullable=False)  # REPRODUCTION/HEALTH/FEED/MOVEMENT/BIOSECURITY/PRODUCTION/FACILITY
    label_en                = Column(String(100), nullable=False)
    label_ko                = Column(String(100))
    label_vi                = Column(String(100))
    required_fields         = Column(JSONB)       # {"field": "required|optional"}
    regional_applicability  = Column(String(50),  default="ALL")  # ALL | comma-sep iso-2
    phase                   = Column(String(10),  default="MVP")  # MVP | PHASE2 | PHASE3
    sort_order              = Column(Integer)


class DiseaseCode(Base):
    __tablename__ = "disease_codes"

    disease_code            = Column(String(20),  primary_key=True)
    woah_code               = Column(String(20))
    label_en                = Column(String(100), nullable=False)
    label_ko                = Column(String(100))
    label_vi                = Column(String(100))
    category                = Column(String(20),  nullable=False)  # VIRAL/BACTERIAL/PARASITIC/METABOLIC/MECHANICAL
    notifiable              = Column(Boolean,      default=False)
    regional_prevalence     = Column(JSONB)        # {"KR":"ENDEMIC","US":"FREE",...}
    typical_mortality_pct   = Column(Numeric(5, 2))
    typical_treatment       = Column(Text)


class VaccineCatalog(Base):
    __tablename__ = "vaccine_catalog"

    vaccine_code            = Column(String(30),  primary_key=True)
    disease_target          = Column(String(20))  # FK → disease_codes.disease_code (soft)
    vaccine_type            = Column(String(20))  # LIVE/KILLED/SUBUNIT/TOXOID
    product_name            = Column(String(100))
    manufacturer            = Column(String(100))
    approved_regions        = Column(ARRAY(Text))  # {"US","KR","SEA",...} or {"ALL"}
    route                   = Column(String(20))   # IM/SC/ORAL/INTRANASAL
    withdrawal_days         = Column(Integer,      default=0)
    notes                   = Column(Text)


class MedicationCatalog(Base):
    __tablename__ = "medication_catalog"

    active_substance        = Column(String(100), primary_key=True)
    atcvet_code             = Column(String(10))  # WHO ATCvet classification
    antibiotic_class        = Column(String(50))  # PENICILLIN/TETRACYCLINE/MACROLIDE/…
    ddda_mg_per_kg          = Column(Numeric(10, 4))  # Defined Daily Dose Animal
    standard_dose_mg_kg     = Column(Numeric(10, 4))
    withdrawal_days_meat    = Column(Integer)
    route                   = Column(String(20))  # ORAL/IM/SC
    vfd_required_us         = Column(Boolean,     default=False)  # US Veterinary Feed Directive
    eu_restricted           = Column(Boolean,     default=False)  # EU critically important / banned
    notes                   = Column(Text)
