# Current State & Healthcare Repurpose Plan
## Women's Nutritional Health Research Platform

---

## What This Codebase Is Today

Holly-morty is a production-ready **AI-powered voice data collection engine** built for financial advisory. It places outbound calls, an AI agent conducts a structured interview, and the full transcript is automatically processed by Claude into a structured profile. A dual-mode dashboard (client + advisor) surfaces the data.

The financial domain is a skin — the underlying pipeline is domain-agnostic.

### Current Stack
| Layer | Technology |
|-------|-----------|
| Voice AI | ElevenLabs Conversational AI (outbound calls + webhooks) |
| Backend | FastAPI (Python 3.11+) |
| LLM Extraction | Anthropic Claude Sonnet (transcript → structured JSON) |
| Database | Azure Cosmos DB (3 containers: conversations, profiles, insights) |
| Frontend | React 19 + TypeScript + Tailwind CSS |
| Deployment | Azure Container Apps / Google Cloud Run |

### Current Data Flow (Financial)
```
Clinician triggers call → ElevenLabs → Holly (AI agent) interviews client
→ Call ends → Webhook fires → FastAPI stores transcript
→ Claude extracts FinancialProfile (200+ fields)
→ Cosmos DB stores profile
→ Advisor Dashboard surfaces structured data
```

---

## Repurpose Goal: Women's Nutrition Research

### Mission
Conduct population-scale research on the nutritional status of women to identify those at risk of nutrition-linked diseases — primarily **anemia**, but also osteoporosis, vitamin D/B12/folate deficiency, and iodine deficiency. The system calls participants, conducts a structured nutritional assessment interview, collects full voice and transcript data, and enables research teams to make sense of the dataset from the admin end.

### Why This Codebase Is a Strong Fit
- Outbound call infrastructure already works end-to-end
- Claude extraction pipeline maps cleanly to health/nutrition schemas
- Webhook + storage pipeline is domain-agnostic
- Admin dashboard (Kanban + filters) maps to research cohort management
- Completeness scoring already exists — repurpose as risk scoring

---

## Target Diseases & Risk Indicators to Screen For

| Condition | Key Dietary/Lifestyle Markers Collected via Voice |
|-----------|--------------------------------------------------|
| **Iron-Deficiency Anemia** | Red meat frequency, leafy greens, menstrual heaviness, fatigue, pallor, breathlessness, cooking in iron pots |
| **Folate Deficiency** | Green vegetable intake, legumes, pregnancy status, alcohol consumption |
| **Vitamin B12 Deficiency** | Vegetarian/vegan diet, dairy/egg intake, numbness/tingling, memory issues |
| **Vitamin D Deficiency** | Sun exposure, dairy, fortified foods, bone pain, indoor lifestyle |
| **Calcium/Osteoporosis Risk** | Dairy intake, calcium-rich foods, fracture history, family history |
| **Iodine Deficiency** | Salt type (iodised vs non), seafood, geographic region, thyroid symptoms |
| **Zinc Deficiency** | Animal protein intake, wound healing, frequent infections, taste changes |

---

## New Architecture: Nutrition Research Platform

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    WOMEN'S NUTRITION RESEARCH PLATFORM                     │
│                                                                             │
│  TRIGGER LAYER                                                              │
│  ┌───────────────────┐   ┌──────────────────────┐   ┌──────────────────┐  │
│  │  Research         │   │  Bulk Scheduler       │   │  Community       │  │
│  │  Coordinator      │   │  (cohort-based cron   │   │  Health Worker   │  │
│  │  (manual trigger) │   │   / Azure Function)   │   │  (field trigger) │  │
│  └────────┬──────────┘   └──────────┬────────────┘   └────────┬─────────┘  │
│           └──────────────────────────┼─────────────────────────┘           │
│                                      ↓                                      │
│                          POST /calls/outbound                               │
│                          { participant_id, phone, study_arm, language }     │
│                                      │                                      │
│  VOICE LAYER                         ↓                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                   ElevenLabs Conversational AI                       │   │
│  │                                                                     │   │
│  │  Agent: "NutriAssist" (new agent — replaces Holly)                  │   │
│  │                                                                     │   │
│  │  Interview Structure:                                               │   │
│  │  1. Introduction + verbal consent collection                       │   │
│  │  2. Demographics (age, location, pregnancy/lactation status)       │   │
│  │  3. Dietary recall (24hr / typical weekly diet)                    │   │
│  │  4. Meal frequency & food group coverage                           │   │
│  │  5. Symptom screen (fatigue, dizziness, pallor, breathlessness)    │   │
│  │  6. Menstrual history (heavy bleeding = iron loss marker)          │   │
│  │  7. Sun exposure, cooking methods, water source                    │   │
│  │  8. Supplement & medication use                                    │   │
│  │  9. Socioeconomic food access indicators                           │   │
│  │  10. Family history of nutritional deficiencies                    │   │
│  │                                                                     │   │
│  │  Call types (separate agent scripts per study arm):                │   │
│  │  • baseline_assessment   (first contact)                           │   │
│  │  • follow_up_3month      (longitudinal tracking)                   │   │
│  │  • targeted_deep_dive    (for high-risk flagged participants)      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│                               [call ends]                                   │
│                                      ↓                                      │
│  PROCESSING LAYER                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        FastAPI Backend                               │   │
│  │                                                                     │   │
│  │  POST /webhooks/nutrition-conversation                              │   │
│  │         │                                                           │   │
│  │         ├─ 1. Verify HMAC-SHA256 signature (MUST enable)           │   │
│  │         ├─ 2. Confirm verbal consent captured in transcript        │   │
│  │         ├─ 3. Store full transcript → conversations container      │   │
│  │         ├─ 4. Claude nutritional extraction:                       │   │
│  │         │      ├─ Parse dietary recall into food groups            │   │
│  │         │      ├─ Map symptoms to deficiency indicators            │   │
│  │         │      ├─ Extract menstrual/reproductive data              │   │
│  │         │      ├─ Score dietary diversity (DDS)                    │   │
│  │         │      ├─ Score minimum dietary diversity for women (MDD-W)│   │
│  │         │      └─ Flag each deficiency risk: low/medium/high       │   │
│  │         ├─ 5. Compute composite risk score per condition           │   │
│  │         ├─ 6. If high-risk for any condition → push to alerts      │   │
│  │         ├─ 7. Store NutritionProfile → profiles container          │   │
│  │         └─ 8. Write audit log (IRB compliance)                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│  STORAGE LAYER                       ↓                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Azure Cosmos DB                              │   │
│  │                                                                     │   │
│  │  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────────┐  │   │
│  │  │ conversations│  │ nutrition_profiles│  │      alerts          │  │   │
│  │  │              │  │                  │  │                      │  │   │
│  │  │ full         │  │ demographics     │  │ participant_id        │  │   │
│  │  │ transcript   │  │ dietary_recall   │  │ condition_flagged     │  │   │
│  │  │ call_meta    │  │ food_groups      │  │ risk_score           │  │   │
│  │  │ consent_     │  │ dds_score        │  │ transcript_excerpt   │  │   │
│  │  │ confirmed    │  │ mddw_score       │  │ resolved / pending   │  │   │
│  │  │ audio_url    │  │ symptoms         │  │                      │  │   │
│  │  │ study_arm    │  │ deficiency_risks │  │                      │  │   │
│  │  │              │  │ menstrual_data   │  │                      │  │   │
│  │  │              │  │ risk_level       │  │                      │  │   │
│  │  │              │  │ study_arm        │  │                      │  │   │
│  │  │              │  │ follow_up_due    │  │                      │  │   │
│  │  └──────────────┘  └──────────────────┘  └──────────────────────┘  │   │
│  │                                                                     │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │                       audit_logs                             │  │   │
│  │  │   every read/write: participant_id, user, timestamp, action  │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                      │                                      │
│  RESEARCH ADMIN LAYER                ↓                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Research Dashboard (React)                        │   │
│  │                                                                     │   │
│  │  ┌──────────────────┐  ┌─────────────────┐  ┌───────────────────┐  │   │
│  │  │  ALERT QUEUE     │  │  COHORT VIEW    │  │  DATASET/ANALYTICS│  │   │
│  │  │                  │  │  (Kanban)       │  │                   │  │   │
│  │  │ High-risk flags  │  │                 │  │ Risk distribution │  │   │
│  │  │ by condition:    │  │ Low | Med | High│  │ by condition      │  │   │
│  │  │                  │  │ (per condition  │  │                   │  │   │
│  │  │ Anemia: 14       │  │  risk level)    │  │ Dietary diversity │  │   │
│  │  │ Vit D: 9         │  │                 │  │ scores histogram  │  │   │
│  │  │ B12: 6           │  │                 │  │                   │  │   │
│  │  │ Folate: 11       │  │                 │  │ Symptom frequency │  │   │
│  │  │                  │  │                 │  │ heatmap           │  │   │
│  │  │ [assign to       │  │                 │  │                   │  │   │
│  │  │  clinician]      │  │                 │  │ Export: CSV/JSON/ │  │   │
│  │  │                  │  │                 │  │ FHIR bundle       │  │   │
│  │  └──────────────────┘  └─────────────────┘  └───────────────────┘  │   │
│  │                                                                     │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │  PARTICIPANT PROFILE VIEW                                    │  │   │
│  │  │  • Full transcript (speaker-labelled)                        │  │   │
│  │  │  • Dietary recall breakdown by food group                    │  │   │
│  │  │  • DDS + MDD-W scores with visual breakdown                  │  │   │
│  │  │  • Per-condition risk cards (anemia, B12, etc.)              │  │   │
│  │  │  • Supporting evidence quotes pulled from transcript         │  │   │
│  │  │  • Menstrual + reproductive data                             │  │   │
│  │  │  • Suggested follow-up actions                               │  │   │
│  │  │  • Researcher notes (editable)                               │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## New Data Model: `NutritionProfile`

Replaces `FinancialProfile` in `models/profile.py`.

```python
class NutritionProfile(BaseModel):
    # Research metadata
    participant_id: str
    study_arm: str           # "baseline_assessment" | "follow_up_3month" | "targeted_deep_dive"
    call_date: datetime
    interviewer_agent_id: str

    # Consent (mandatory before any data is stored)
    consent_given: bool
    consent_timestamp: datetime
    consent_method: str      # "verbal_confirmed"

    # Demographics
    age: Optional[int]
    location_region: Optional[str]
    location_urban_rural: Optional[str]   # "urban" | "peri-urban" | "rural"
    pregnancy_status: Optional[str]       # "pregnant" | "lactating" | "neither"
    weeks_pregnant: Optional[int]
    number_of_children: Optional[int]
    education_level: Optional[str]
    household_size: Optional[int]

    # Dietary recall (24hr and/or typical week)
    dietary_recall_24hr: Optional[str]    # raw narrative
    food_groups_consumed: List[str]       # e.g. ["cereals", "legumes", "leafy_greens", "flesh_foods"]
    meal_frequency_per_day: Optional[int]
    dietary_diversity_score: Optional[int]          # DDS (0-12)
    minimum_dietary_diversity_women: Optional[bool] # MDD-W: ≥5 food groups out of 10

    # Food group detail
    iron_rich_foods_frequency: Optional[str]        # "daily" | "weekly" | "rarely" | "never"
    vitamin_c_foods_frequency: Optional[str]        # enhances iron absorption
    tea_coffee_with_meals: Optional[bool]            # inhibits iron absorption
    calcium_rich_foods_frequency: Optional[str]
    dairy_intake_frequency: Optional[str]
    animal_protein_frequency: Optional[str]
    leafy_greens_frequency: Optional[str]
    legumes_frequency: Optional[str]
    fortified_foods_consumed: Optional[bool]
    iodised_salt_used: Optional[bool]
    seafood_frequency: Optional[str]
    sun_exposure_hours_per_day: Optional[float]
    cooking_method: Optional[str]                   # "iron pot" is a protective factor for anemia

    # Supplement & medication
    iron_supplement: Optional[bool]
    folate_supplement: Optional[bool]
    vitamin_d_supplement: Optional[bool]
    multivitamin: Optional[bool]
    other_supplements: List[str]
    current_medications: List[str]

    # Socioeconomic / food access
    food_insecurity_reported: Optional[bool]
    meals_skipped_last_week: Optional[int]
    market_access: Optional[str]         # "easy" | "difficult" | "very_difficult"
    primary_food_source: Optional[str]   # "market" | "own_farm" | "aid" | "mixed"

    # Symptoms screen
    fatigue_level: Optional[int]                    # 1-10 self-reported
    dizziness_reported: Optional[bool]
    shortness_of_breath_reported: Optional[bool]
    pallor_reported: Optional[bool]                 # pale skin/nails/gums
    cold_intolerance: Optional[bool]
    pica_reported: Optional[bool]                   # craving non-food items (strong anemia marker)
    bone_pain_reported: Optional[bool]
    muscle_cramps_reported: Optional[bool]
    tingling_numbness: Optional[bool]               # B12 marker
    memory_concentration_issues: Optional[bool]     # B12 marker
    thyroid_symptoms: Optional[str]                 # iodine deficiency
    hair_nail_changes: Optional[bool]

    # Menstrual & reproductive history
    menstrual_status: Optional[str]       # "regular" | "irregular" | "absent" | "postmenopausal"
    heavy_menstrual_bleeding: Optional[bool]        # major iron-loss risk factor
    cycle_length_days: Optional[int]
    days_of_bleeding: Optional[int]
    recent_birth_months_ago: Optional[int]

    # Family & medical history
    family_history_anemia: Optional[bool]
    family_history_osteoporosis: Optional[bool]
    diagnosed_conditions: List[str]       # pre-existing diagnoses
    previous_anemia_diagnosis: Optional[bool]

    # Deficiency risk scores (computed by Claude from full transcript)
    anemia_risk: Optional[str]            # "low" | "medium" | "high"
    folate_deficiency_risk: Optional[str]
    vitamin_b12_risk: Optional[str]
    vitamin_d_risk: Optional[str]
    calcium_risk: Optional[str]
    iodine_deficiency_risk: Optional[str]
    zinc_deficiency_risk: Optional[str]

    # Composite
    overall_nutritional_risk: Optional[str]  # "low" | "medium" | "high" | "critical"
    risk_evidence: List[str]                 # quotes from transcript supporting the risk score
    recommended_follow_up: List[str]
    researcher_notes: Optional[str]
```

---

## Key Code Changes Required

### Files to Modify

| File | Change |
|------|--------|
| `models/profile.py` | Replace `FinancialProfile` with `NutritionProfile` (schema above) |
| `services/profile_extraction.py` | Swap Claude system prompt to nutritional extraction guidelines |
| `routers/webhooks.py` | Update to new schema; add consent gate; enable HMAC verification |
| `routers/profiles.py` | Update search endpoints (by risk level, by condition, by study arm) |
| `routers/calls.py` | Add `study_arm` and `language` fields to call request |
| `core/cosmos.py` | Add `alerts` container alongside conversations/profiles |
| `web/components/AdvisorDashboard.tsx` | Repurpose to `ResearchDashboard.tsx` |
| `web/types.ts` | Update TypeScript interfaces to match new schema |

### Files to Create

| File | Purpose |
|------|---------|
| `routers/alerts.py` | Alert queue: list unresolved, resolve, assign to researcher |
| `services/risk_stratification.py` | Rule-based + Claude-assisted risk scoring per condition |
| `services/fhir_export.py` | FHIR R4 bundle export of nutrition profiles |
| `web/components/ResearchDashboard.tsx` | New clinical/research admin view |
| `web/components/AlertQueue.tsx` | Real-time alert management panel |
| `web/components/DatasetExport.tsx` | Cohort-level analytics + CSV/JSON/FHIR export |

---

## Claude Extraction Prompt (Updated System Prompt)

The only change to `services/profile_extraction.py` is the system prompt passed to Claude:

```
You are a clinical nutrition researcher assistant. You will receive a transcript
of a voice interview conducted with a woman participant in a nutritional health study.

Your task is to extract a structured NutritionProfile JSON from the transcript.

Guidelines:
- Extract all dietary recall data: food types, frequency, preparation methods
- Identify and score food group diversity (DDS: 0-12, MDD-W: true if ≥5 of 10 WHO groups)
- Map reported symptoms to likely nutritional deficiencies using evidence-based associations:
    * Fatigue + pallor + heavy periods + low red meat → anemia risk HIGH
    * Vegan/vegetarian + tingling/numbness + memory issues → B12 risk HIGH
    * Minimal sun + bone pain + no dairy → vitamin D risk HIGH
    * Pregnancy + low green vegetables + no supplements → folate risk HIGH
    * Non-iodised salt + coastal-distant region + thyroid symptoms → iodine risk HIGH
- Always include risk_evidence: direct quotes from the transcript that support each risk score
- If consent was NOT verbally confirmed, set consent_given: false and do not extract clinical data
- Use null for any field not discussed in the interview — do not guess
- Output valid JSON only, matching the NutritionProfile schema exactly
```

---

## New API Endpoints

```
POST /calls/outbound              → unchanged, add study_arm + language fields
POST /webhooks/nutrition-conversation → replaces holly-conversation

GET  /profiles                    → all nutrition profiles (paginated)
GET  /profiles/{participant_id}   → single profile
GET  /profiles/search/by-risk     → filter by overall_nutritional_risk
GET  /profiles/search/by-condition → filter by anemia_risk, vitamin_d_risk, etc.
GET  /profiles/search/by-study-arm → filter by baseline / follow_up / targeted
GET  /profiles/export/csv         → full dataset as CSV for research analysis
GET  /profiles/export/fhir        → FHIR R4 bundle

GET  /alerts                      → all unresolved high/critical risk alerts
POST /alerts/{id}/resolve         → mark resolved with researcher notes
GET  /analytics/cohort-summary    → aggregate stats: risk distribution, DDS histogram
GET  /analytics/condition-breakdown → counts per condition risk level
```

---

## Implementation Phases

### Phase 1 — Core Reuse (Week 1-2)
- [ ] Create new ElevenLabs agent "NutriAssist" with nutrition interview script
- [ ] Enable HMAC webhook signature verification (already coded, just uncommented)
- [ ] Replace `FinancialProfile` with `NutritionProfile` schema
- [ ] Update Claude extraction prompt for nutritional data
- [ ] Update `routers/calls.py` to accept `study_arm` + `language`

### Phase 2 — Safety & Research Logic (Week 2-3)
- [ ] Add `alerts` Cosmos container + `routers/alerts.py`
- [ ] Build `services/risk_stratification.py` with condition-specific rules
- [ ] Add consent gate: block profile extraction if consent_given is false
- [ ] Add audit logging middleware

### Phase 3 — Research Dashboard (Week 3-5)
- [ ] Build `ResearchDashboard.tsx` with cohort Kanban (risk-based columns)
- [ ] Build `AlertQueue.tsx` component
- [ ] Build per-condition filter panel (replace financial filters)
- [ ] Add transcript viewer with risk evidence highlighting
- [ ] Add DDS / MDD-W score visualisations

### Phase 4 — Dataset & Export (Week 5-6)
- [ ] `GET /profiles/export/csv` — full dataset for offline analysis
- [ ] `GET /analytics/cohort-summary` — aggregate stats endpoint
- [ ] `GET /profiles/export/fhir` — FHIR R4 export
- [ ] Dataset analytics view in dashboard (histograms, heatmaps)

---

## Compliance & Ethics Checklist

| Requirement | Status | Action |
|-------------|--------|--------|
| Verbal consent captured in transcript | Not present | Add to agent script; gate extraction on it |
| HMAC webhook verification | Coded but disabled | Enable in `routers/webhooks.py` |
| IRB / Ethics approval documentation | Not present | Required before any data collection |
| Data retention policy | Not present | Set Cosmos TTL; define retention period |
| Participant anonymisation | Not present | Separate PII container; use participant_id not name in analytics |
| BAA with ElevenLabs | Not confirmed | Required — ElevenLabs does offer HIPAA BAA |
| BAA with Anthropic | Not confirmed | Required — Anthropic offers BAA for healthcare |
| Audit logging | Not present | Add middleware to log all data access |
| Language/literacy access | Not present | Configure ElevenLabs multilingual agents |

---

## What Stays Exactly the Same

- ElevenLabs outbound call infrastructure (`routers/calls.py`)
- Cosmos DB multi-container pattern (`core/cosmos.py`)
- Webhook receive → store → extract → profile pipeline (`routers/webhooks.py` structure)
- FastAPI app setup and routing (`main.py`)
- React + TypeScript frontend architecture
- Polling pattern for real-time updates (already in `Dashboard.tsx`)
- Pagination on all list endpoints
- Azure Container Apps deployment
