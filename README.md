# Sunwave CRM Dashboard

**Live URL:** https://icy-moss-07b041e10.7.azurestaticapps.net/crm/

This is Provident Healthcare's CRM & Productivity dashboard. It takes raw data from Sunwave (our EMR/CRM system), stores it in a SQL database, and shows it as interactive charts and tables on a web page.

---

## How It Works (The Big Picture)

Think of it like a pipeline with 3 steps:

```
Step 1: COLLECT                Step 2: STORE              Step 3: SHOW
───────────────               ─────────────              ──────────────
Sunwave EMR                   Azure SQL DB               This Dashboard
(the source)                  (the warehouse)            (the display)
     │                              │                          │
     │  Sunwave APIs               │  API queries             │  Browser
     │  (HTTP GET calls)           │  (SELECT * FROM ...)     │  (fetch JSON)
     ▼                              ▼                          ▼
strive-ur-api              sunwave_opportunities         crm/index.html
Azure Function             crm_timeline                  (10 tabs of
App syncs data             sunwave_sync_log              charts & tables)
on a schedule              (+ 25 other tables)
```

**Step 1 — Collect:** An Azure Function App called `strive-ur-api` calls Sunwave's REST APIs on a schedule. Sunwave responds with JSON arrays of patient records, opportunities, timeline events, etc.

**Step 2 — Store:** The function app takes each JSON row, maps field names (e.g. Sunwave calls it `"patient name"`, we store it as `patient_name`), and upserts it into Azure SQL tables using T-SQL `MERGE` statements.

**Step 3 — Show:** This dashboard (a static HTML page) calls the function app's `/api/dashboard/crm` endpoint, gets back all the data as JSON, and renders it into KPI cards, tables, and charts using Chart.js.

---

## The Two Main Tables (CRM Dashboard)

The CRM dashboard uses exactly **2 SQL tables**. Everything you see on screen comes from these two.

### Table 1: `sunwave_opportunities`

This table holds **every patient opportunity** (think of an opportunity as "someone contacted us about treatment"). Each row is one person.

**Where does it come from?** Sunwave API: `GET /api/opportunities/createdon/from/{date}/until/{date}`

**How many columns?** 147 columns. Here are the important ones:

| Column Name | What It Stores | Example |
|---|---|---|
| `opportunity_id` | Unique ID from Sunwave | `1146750` |
| `patient_name` | Patient's full name | `James Edwards` |
| `first_name` | First name | `James` |
| `last_name` | Last name | `Edwards` |
| `created_on` | When the opportunity was created | `2026-04-27 10:30:00` |
| `admission_date` | When the patient was admitted (if they were) | `2026-05-01` |
| `status` | The outcome — what happened | `Admitted`, `Lost`, `Abandoned`, `Active` |
| `stage` | Where they are in the pipeline | `Created`, `Pre-Screen`, `VOB`, `Scheduled`, `No Contact Made` |
| `level_of_care` | What level of care they need | `Discharged`, `PHP`, `IOP`, `RTC` |
| `insurance_name` | Their insurance company | `ANTHEM BCBS IN MCD` |
| `referral_source` | Who referred them to us | `Website`, `Psychology Today` |
| `assigned_to` | Which staff member owns this opportunity | `Shreenda Johnson` |
| `lost_reason` | If outcome=Lost, why we lost them | `No Contact Made`, `Insurance` |
| `abandoned_reason` | If outcome=Abandoned, why they left | `No Show`, `Patient Declined` |
| `phone` | Patient phone number | `317-555-1234` |
| `email` | Patient email | `patient@email.com` |
| `realm` | Which facility/location | `Provident Behavioral Health` |
| `synced_at` | When this row was last updated by our sync | `2026-08-06 06:00:15` |

**Other columns** include: `caller_firstname`, `caller_lastname`, `subscriber_firstname`, `subscriber_insurance_id`, `guardian_name`, `guardian_phone`, `patient_dob`, `google_lead_source`, `admission_date_raw`, and ~120 more detailed fields.

**How the dashboard shows it on screen (JSON mapping):**

When the API sends data to the browser, it renames columns to short keys to save bandwidth:

| SQL Column | JSON Key Sent to Browser |
|---|---|
| `opportunity_id` | `id` |
| `patient_name` | `name` |
| `created_on` | `co` |
| `admission_date` | `admit` |
| `status` | `outcome` |
| `stage` | `stage` |
| `level_of_care` | `loc` |
| `insurance_name` | `ins` |
| `referral_source` | `ref` |
| `lost_reason` | `lost_r` |
| `abandoned_reason` | `aband_r` |
| `assigned_to` | `rep` |

---

### Table 2: `crm_timeline`

This table holds **every activity/event** that happened on an opportunity. Think of it as a diary — every call, note, email, workflow change, and task is one row.

**Where does it come from?** Sunwave API: `GET /api/opportunities/{id}/timeline` (called once per opportunity ID)

**How many columns?** 41 columns. Here are the important ones:

| Column Name | What It Stores | Example |
|---|---|---|
| `sunwave_timeline_id` | Unique ID for this event | `TL-98234` |
| `opportunity_id` | Which opportunity this belongs to | `1146750` |
| `source_type` | What kind of record this is linked to | `Opportunity`, `Referral` |
| `source_id` | The ID of the linked record | `1146750` |
| `activity_type` | What kind of activity this is | `Call`, `Note`, `Email`, `Task`, `Workflow`, `Sms`, `Wave`, `Meeting` |
| `description` | Free-text description of what happened | `Called patient, left voicemail` |
| `created_by_name` | Who did this activity | `Shreenda Johnson` |
| `created_by_id` | Sunwave user ID of who did it | `USR-4521` |
| `activity_date` | When the activity happened | `2026-07-15 14:30:00` |
| `created_on` | When this record was created in Sunwave | `2026-07-15 14:32:00` |
| `workflow_status` | For Workflow events, the new status | `Scheduled`, `Admitted` |
| `task_subject` | For Task events, the task title | `Follow up with insurance` |
| `task_status` | For Task events, the status | `Open`, `Completed`, `Pending` |
| `task_due_date` | For Task events, when it's due | `2026-07-20` |
| `task_completed_on` | For Task events, when it was finished | `2026-07-19` |
| `task_type` | For Task events, what kind | `Follow Up`, `General` |
| `assigned_to` | Who the task is assigned to | `Gabrielle Joyce` |
| `call_direction` | For Call events, inbound or outbound | `Outbound` |
| `call_outcome` | For Call events, what happened | `Left Voicemail`, `Connected` |
| `contact_name` | Who was contacted | `John Smith` |
| `contact_email` | Contact's email | `john@email.com` |
| `contact_phone` | Contact's phone | `317-555-5678` |
| `campaign_name` | Marketing campaign (if any) | `Google Ads Q3` |
| `reminder_date_time` | When a reminder is set for | `2026-07-18 09:00:00` |
| `status` | General status field | `Active` |
| `response` | Response text (for SMS/Email) | `Yes, I am interested` |
| `from_phone` | For SMS, the sending number | `+13175551234` |
| `related_task_id` | If this event links to another task | `TASK-1234` |
| `synced_at` | When this row was last updated by our sync | `2026-08-06 06:00:45` |

**How the dashboard shows it on screen (JSON mapping):**

| SQL Column | JSON Key Sent to Browser |
|---|---|
| `opportunity_id` or `source_id` | `oid` |
| `sunwave_timeline_id` | `aid` |
| `activity_type` | `type` |
| `task_subject` | `subj` (truncated to 140 chars) |
| `description` | `text` (truncated to 400 chars) |
| `created_by_name` | `by` |
| `workflow_status` | `wf` |
| `activity_date` | `date` |
| `source_type` | `assoc` |
| `task_type` | `task_type` |
| `task_status` | `task_status` |
| `task_due_date` | `task_due_date` |
| `reminder_date_time` | `reminder_date_time` |
| `assigned_to` | `assigned_to_name` |

**Derived arrays** (computed from `crm_timeline` by the API before sending to the browser):

| Array | How It's Built |
|---|---|
| `USERS` | All distinct `created_by_name` + `assigned_to` values from timeline |
| `TASKS` | Timeline rows where `activity_type = 'Task'`, with extra fields: `is_open` (true if task_status is open/pending/empty) |

---

### Table 3: `sunwave_sync_log` (Audit/Logging)

This table records every sync run — when it happened, how many rows, and whether it succeeded.

| Column | What It Stores | Example |
|---|---|---|
| `endpoint` | Which API was synced | `opportunities`, `opportunity-timeline`, `crm-timeline` |
| `row_count` | How many rows were inserted or updated | `836` |
| `status` | Did it work? | `success`, `partial`, `error` |
| `error_message` | If something went wrong, what happened | `Timeout after 230s` |
| `synced_at` | When the sync ran | `2026-08-06 06:00:00` |
| `from_date` | Start of the date range that was synced | `2026-07-22` |
| `until_date` | End of the date range | `2026-08-06` |

---

## Sunwave API Details

### What Is Sunwave?

Sunwave is the EMR (Electronic Medical Records) / CRM system that Provident Healthcare uses. It stores all patient data, opportunities, referrals, billing, etc. We pull data from it using their REST API.

### Connection Details

| Setting | Value |
|---|---|
| **Base URL** | `https://emr.sunwavehealth.com/SunwaveEMR` (stored in `SUNWAVE_BASE_URL` env var) |
| **Auth Method** | Custom Digest authentication (HMAC-SHA512 signed token) |
| **Auth Header** | `Authorization: Digest {token}` |
| **Response Format** | JSON arrays |
| **Rate Limiting** | Returns HTTP 429 when exceeded; our code retries 3 times with 5s/10s/15s backoff |

### Authentication (How We Log In to Sunwave)

The API uses a custom token-based auth (not standard OAuth). Here's how it works:

1. Build a "seed" string: `userId:clientId:base64(date):clinicId:transactionId:base64(md5(""))`
2. Sign it with HMAC-SHA512 using the `clientSecret`
3. Base64-encode the result (URL-safe)
4. Send it as: `Authorization: Digest {base64token}`

**Required environment variables** (stored in Azure Function App settings):

| Variable | What It Is |
|---|---|
| `SUNWAVE_BASE_URL` | The Sunwave server URL |
| `SUNWAVE_USER_ID` | Our Sunwave service account user ID |
| `SUNWAVE_CLIENT_ID` | 32-character client identifier from Sunwave |
| `SUNWAVE_CLIENT_SECRET` | 256-character HMAC secret from Sunwave |
| `SUNWAVE_CLINIC_ID` | Which clinic/realm we're pulling data for |

### CRM-Related API Endpoints

These are the Sunwave APIs that feed the CRM dashboard:

#### 1. Opportunities (by Created Date)

```
GET /api/opportunities/createdon/from/{yyyy-MM-dd}/until/{yyyy-MM-dd}
```

- **What it returns:** Every opportunity created in the date range
- **Target table:** `sunwave_opportunities`
- **Key column:** `opportunity_id`
- **Fields returned:** 124 fields (patient name, stage, outcome, insurance, referral source, assigned rep, dates, contact info, etc.)
- **Max date range:** 365 days per call (chunked automatically if larger)
- **When it runs:** Daily at 6:00 AM UTC, looking back 15 days

#### 2. Active Opportunities

```
GET /api/opportunities/active/createdon/from/{yyyy-MM-dd}/until/{yyyy-MM-dd}
```

- **What it returns:** Only active/open opportunities
- **Target table:** `sunwave_opportunities` (same table, upserted by `opportunity_id`)
- **When it runs:** Daily at 6:00 AM UTC

#### 3. Opportunity Timeline (Per-ID)

```
GET /api/opportunities/{opportunityId}/timeline
```

- **What it returns:** Every activity (call, note, email, task, workflow change, SMS, meeting) for that one opportunity
- **Target table:** `crm_timeline`
- **Key column:** `sunwave_timeline_id`
- **Fields returned:** 41 fields per event
- **How it runs:** Loops through ALL opportunity IDs from `sunwave_opportunities`, calling this API once per ID with a 100ms delay between calls
- **When it runs:** Daily at 6:00 AM UTC, AFTER all other syncs finish
- **Known issue:** With 836+ opportunities, this takes a long time and can time out

### All Other Sunwave API Endpoints

The sync system pulls data from **30+ Sunwave API endpoints** into **27 SQL tables**. Here is the full list:

| # | Endpoint Key | Sunwave API Path | Target SQL Table | Schedule |
|---|---|---|---|---|
| 1 | `census-active` | `/api/census/active/from/{from}/until/{until}` | `sunwave_census_active` + `records` | Hourly |
| 2 | `census-admitted` | `/api/census/admitted/from/{from}/until/{until}` | `sunwave_census_admitted` + `records` | Hourly |
| 3 | `census-discharged` | `/api/census/discharged/from/{from}/until/{until}` | `sunwave_census_discharged` + `records` | Hourly |
| 4 | `auth-days` | `/api/reports/auth_days/from/{from}/until/{until}` | `sunwave_auth_days` + `records` | Hourly |
| 5 | `ur-report` | `/api/reports/ur_report/from/{from}/until/{until}` | `sunwave_ur_report` + `records` | Hourly |
| 6 | `users` | `/api/users` | `coordinators` | Daily 6 AM |
| 7 | `realms` | `/api/realms` | `sunwave_realms` | Daily 6 AM |
| 8 | `bedboard` | `/api/bedboard/buildings` | `sunwave_bedboard` | Daily 6 AM |
| 9 | `forms-list` | `/api/forms` | `sunwave_forms` | Daily 6 AM |
| 10 | `diagnosis-changes` | `/api/reports/diagnosis_changes/from/{from}` | `sunwave_diagnosis_changes` | Daily 6 AM |
| 11 | `program-changes` | `/api/reports/program_changes/from/{from}` | `sunwave_program_changes` | Daily 6 AM |
| 12 | `deleted-forms` | `/api/reports/deleted_forms/from/{from}/until/{until}` | `sunwave_deleted_forms` | Daily 6 AM |
| 13 | `modified-forms` | `/api/reports/modified_forms/from/{from}/until/{until}` | `sunwave_modified_forms` | Daily 6 AM |
| 14 | `billing` | `/api/billing/arreport/from/{from}/until/{until}/billingentityid/{id}` | `sunwave_billing` | Daily 6 AM |
| 15 | `billing-summary` | `/api/billing/arreportsummary/from/{from}/until/{until}/billingentityid/{id}` | `sunwave_billing_summary` | Daily 6 AM |
| 16 | `payments-by-payment-date` | `/api/paymentsreport/paymentDate/from/{from}/until/{until}` | `sunwave_payments` | Daily 6 AM |
| 17 | `payments-by-deposit-date` | `/api/paymentsreport/depositDate/from/{from}/until/{until}` | `sunwave_payments` | Daily 6 AM |
| 18 | `leads-active` | `/api/leads/active/from/{from}/until/{until}` | `sunwave_leads` | Daily 6 AM |
| 19 | `leads-qualified` | `/api/leads/qualified/from/{from}/until/{until}` | `sunwave_leads` | Daily 6 AM |
| 20 | `leads-lost` | `/api/leads/lost/from/{from}/until/{until}` | `sunwave_leads` | Daily 6 AM |
| 21 | `opportunities` | `/api/opportunities/createdon/from/{from}/until/{until}` | `sunwave_opportunities` | Daily 6 AM |
| 22 | `opportunities-active` | `/api/opportunities/active/createdon/from/{from}/until/{until}` | `sunwave_opportunities` | Daily 6 AM |
| 23 | `referrals-active` | `/api/referrals/status/active` | `sunwave_referrals` | Daily 6 AM |
| 24 | `referrals-inactive` | `/api/referrals/status/inactive` | `sunwave_referrals` | Daily 6 AM |
| 25 | `referral-timeline` | `/api/referrals/timeline/from/{from}/until/{until}` | `sunwave_referral_timeline` | Daily 6 AM |
| 26 | `incidents-created` | `/api/incidentreports/created/from/{from}/until/{until}` | `sunwave_incident_reports` | Daily 6 AM |
| 27 | `incidents-reported` | `/api/incidentreports/reported/from/{from}/until/{until}` | `sunwave_incident_reports` | Daily 6 AM |
| 28 | `assessment-scores` | `/api/assessmentscoresreport/from/{from}/until/{until}/assessment_name/{name}` | `sunwave_assessment_scores` | Daily 6 AM |
| 29 | `group-notes` | `/api/getgroupnotes/{date}` | `sunwave_group_notes` | Daily 6 AM |
| 30 | `patient-loa` | `/api/patients/loa/from/{from}/until/{until}` | `sunwave_patient_loa` | Daily 6 AM |
| 31 | `opportunity-timeline` | `/api/opportunities/{id}/timeline` (per-ID loop) | `crm_timeline` | Daily 6 AM (after all above) |
| 32 | `referral-id-timeline` | `/api/referrals/{id}/timeline` (per-ID loop) | `crm_timeline` | Daily 6 AM (after all above) |

---

## Sync Schedules (When Data Gets Updated)

There are **2 automatic timers** that pull data from Sunwave:

### Timer 1: Hourly Records Sync

```
Schedule: 0 0 * * * *    (every hour, on the hour)
Lookback: 2 days
```

This runs every hour and only syncs the 5 "records" endpoints (census + auth + UR). These are the most time-sensitive because they track who is currently admitted.

**Endpoints synced:** `census-active`, `census-admitted`, `census-discharged`, `auth-days`, `ur-report`

### Timer 2: Daily Full Sync

```
Schedule: 0 0 6 * * *    (every day at 6:00 AM UTC / 2:00 AM ET)
Lookback: 15 days
```

This runs once a day and syncs EVERYTHING. It runs in this order:

1. First, sync all 21 "daily" endpoints (users, opportunities, referrals, billing, etc.)
2. Then, sync CRM timelines for all opportunity IDs (loops through each one)
3. Then, sync CRM timelines for all referral IDs

**Why 15-day lookback?** To catch any records that were created or modified in the last 15 days. This handles cases where someone edits a week-old record in Sunwave.

**Date range chunking:** Some endpoints can only handle a limited date range per call. The system automatically splits large ranges:

| Max Days Per Call | Endpoints |
|---|---|
| 14 days | diagnosis-changes, program-changes, deleted-forms, modified-forms, referral-timeline |
| 30 days | auth-days, ur-report, incidents, patient-loa |
| 59 days | payments |
| 365 days | census, leads, opportunities |

### Manual Sync

You can also trigger syncs manually via HTTP:

```
GET /api/sunwave/sync/{endpoint}?from=2026-01-01&until=2026-08-01
GET /api/sunwave/sync-crm-timeline?source=opportunity&limit=50&offset=0
GET /api/sunwave/sync-all
GET /api/sunwave/sync-records        (runs the hourly set)
GET /api/sunwave/sync-daily          (runs the daily set)
```

---

## Dashboard API Endpoints

These are the API endpoints that the dashboard calls to get data:

| Endpoint | What It Returns |
|---|---|
| `GET /api/dashboard/crm` | 4 arrays: `opps` (opportunities), `acts` (timeline activities), `users` (distinct staff names), `tasks` (activities where type=Task) + `meta` (counts, refresh timestamp) |
| `GET /api/dashboard/crm-audit` | Table schemas, record stats (count/min/max dates), sync logs, activity type breakdown, task status breakdown |
| `GET /api/dashboard/view/raw-opportunities` | All rows from `sunwave_opportunities` (for XLSX download) |
| `GET /api/dashboard/view/raw-timeline` | All rows from `crm_timeline` (for XLSX download) |

**API Base URL:** `https://strive-ur-api-gdhbd0htb8ghb8ez.canadacentral-01.azurewebsites.net`

**Function App:** `strive-ur-api` (deployed from the [UR-Tracking-dev](https://github.com/Provident-Healthcare-Consulting/UR-Tracking-dev) repo)

---

## Dashboard Tabs

The dashboard has **10 tabs**. Here's what each one shows and where the data comes from:

### 1. Overview (Both tables)

| Visual | Data Source |
|---|---|
| Created / Admitted / Admit Rate / In Pipeline / Lost KPIs | `sunwave_opportunities` -- counts by outcome |
| Activities KPI | `crm_timeline` -- total count |
| Stuck Opportunities | Both -- active opps with no human activity for >7 days |
| Open CRM Tasks | `crm_timeline` -- tasks where status is open/pending |
| Activity Leaderboard | `crm_timeline` -- grouped by `created_by_name` |
| Recent Admissions | Both -- admitted opps + last human activity as "closer" |

### 2. Pipeline & Funnel (sunwave_opportunities only)

| Visual | Data Source |
|---|---|
| Stage Distribution funnel + trend | Opps grouped by `stage` |
| Outcome Distribution + trend | Opps grouped by `status` (outcome) |
| Lost Reason breakdown | Lost opps grouped by `lost_reason` |
| Abandoned Reason breakdown | Abandoned opps grouped by `abandoned_reason` |

### 3. User Productivity (crm_timeline only)

| Visual | Data Source |
|---|---|
| Active Users / Total Activities / Median KPIs | Activities grouped by user |
| User Productivity Table | Activities split by type (Call/Note/Email/SMS/Task/Meeting) per user |
| Per-user activity trend | Activities by user over time |

### 4. User Effectiveness (Both tables)

| Visual | Data Source |
|---|---|
| Opps Touched per user | Distinct `opportunity_id` per user from timeline |
| Admits Credited per user | Admitted opps + all activities on those opps |
| Avg Response Time | Time from opportunity created to first activity by each user |

### 5. Opportunity Flow (Both tables)

| Visual | Data Source |
|---|---|
| Searchable opportunity list | `sunwave_opportunities` -- name, ID, stage, outcome, LOC, insurance |
| Expandable timeline per opp | `crm_timeline` -- all activities matching that opportunity ID |
| Task Flag / Stage Corrections | Derived from activity patterns |

### 6. Activity Trends (crm_timeline only)

| Visual | Data Source |
|---|---|
| Activity by Type heatmap | Activities bucketed by date and `activity_type` |
| Hour x Day-of-Week heatmap | Activities by hour and weekday |
| Per-user activity trend | Activities by user over time |

### 7. Velocity (Mostly sunwave_opportunities)

| Visual | Data Source |
|---|---|
| Time-to-Schedule (TTS) | `created_on` to scheduled date |
| Time-to-Admit (TSA) | Scheduled date to `admission_date` |
| Total Time-to-Admit (TTA) | `created_on` to `admission_date` |
| First-Touch Response Time | Both -- `created_on` to first human activity |

### 8. Composition (sunwave_opportunities only)

| Visual | Data Source |
|---|---|
| Top 5 Referral Sources trend | Opps grouped by `referral_source` over time |
| Insurance Mix on Admits | Admitted opps grouped by `insurance_name` |
| LOC Mix on Admits | Admitted opps grouped by `level_of_care` |

### 9. Audit (Both tables + sync log)

| Visual | Data Source |
|---|---|
| Filtered vs Total KPIs | Both tables -- filtered count vs DB total |
| Outcome breakdown | `sunwave_opportunities` grouped by `status` |
| Record range cards | MIN/MAX `created_on` and `synced_at` for both tables |
| Sync log table | `sunwave_sync_log` -- last 50 entries |
| Schema tables | `INFORMATION_SCHEMA.COLUMNS` for both tables |
| Raw data samples | First 20 rows from each table (filtered) |
| XLSX download buttons | Downloads ALL rows from `sunwave_opportunities` or `crm_timeline` |

### 10. Timeline Dashboard (crm_timeline only)

| Visual | Data Source |
|---|---|
| Total Activities / Opps Touched / Calls / Notes / Workflow Moves / Active Staff KPIs | `crm_timeline` -- counts and distinct values |
| Activities by Type table | `crm_timeline` grouped by `activity_type` with count and % |
| Monthly Activity Trend | `crm_timeline` grouped by `YYYY-MM` of `activity_date` |
| Staff Activity Volume (Top 15) | `crm_timeline` grouped by `created_by_name` with Calls/Notes breakdown |

**Note:** This tab ignores the "Human Only" filter so Workflow and Wave events are always included in the counts.

---

## Sidebar Filters

The left sidebar has filters that apply to most tabs:

| Filter | What It Does | Options |
|---|---|---|
| **Period** | Only show data from this time range | 7D, 14D, 30D, 90D, 180D, 1Y, YTD, All, Custom |
| **Granularity** | How to group time-series charts | Day, Week, Month |
| **Outcome** | Only show opportunities with this outcome | All, Active, Admitted, Lost, Abandoned |
| **User** | Only show activities by this staff member | Dropdown of all staff |
| **View** | Human Only (hide automated workflow events) or All Activity | Human, All |

---

## Authentication

The dashboard uses **Microsoft Entra ID** (formerly Azure AD) single sign-on. Only users from Provident's Azure AD tenant can access it.

| Setting | Value |
|---|---|
| **Auth Library** | MSAL Browser v3.10.0 |
| **Client ID** | `debd63be-2397-4d6e-adb1-381574e7352b` (UserPermissionManagement app) |
| **Tenant ID** | `063ab74f-56d1-429a-b96d-a24a572025de` (Provident Healthcare) |
| **Allowed Domains** | `@gshealthcarellc.com` and `@providenthcc.com` |
| **Login Method** | Popup (not redirect) |
| **Session Storage** | Browser `sessionStorage` (cleared when tab closes) |

---

## Deployment

| Component | Where It Lives |
|---|---|
| **Dashboard (this repo)** | Azure Static Web App at `icy-moss-07b041e10.7.azurestaticapps.net` |
| **API (strive-ur-api)** | Azure Function App at `strive-ur-api-gdhbd0htb8ghb8ez.canadacentral-01.azurewebsites.net` |
| **API Source Code** | [UR-Tracking-dev](https://github.com/Provident-Healthcare-Consulting/UR-Tracking-dev) repo |
| **Database** | Azure SQL (connection string in Function App settings) |

**How deployment works:**
1. Push to `main` branch of this repo
2. GitHub Actions workflow runs automatically
3. Azure Static Web Apps deploys the files to `icy-moss-07b041e10.7.azurestaticapps.net`

**CORS:** The Function App must have `https://icy-moss-07b041e10.7.azurestaticapps.net` in its CORS allowed origins, otherwise the dashboard can't fetch data.

---

## Files in This Repo

| File | What It Is |
|---|---|
| `index.html` | Root page -- just redirects to `/crm/` |
| `crm/index.html` | The entire CRM dashboard (single HTML file with inline CSS/JS) |
| `README.md` | This file |
| `.github/workflows/azure-static-web-apps-icy-moss-07b041e10.yml` | CI/CD deployment workflow |

---

## How the SQL Upsert Works

When syncing data from Sunwave, we don't just INSERT rows. We use SQL `MERGE` statements (also called "upsert") which means:

- **If the row already exists** (matched by the key column like `opportunity_id`): UPDATE it with the new values
- **If the row doesn't exist yet**: INSERT it as a new row

This means running a sync twice with the same data won't create duplicates -- it just updates existing rows.

**Protected columns** (never overwritten by sync): `decision`, `denial_reason`, `denial_sub`, `denial_date`, `avoidable`, `appeal_filed`, `appeal_outcome`, `stage`, `wf_notes`, `notes`, `priority`, `next_task`, `next_due`, `owner`, `dept`. These are fields that staff edit manually in our system, so the sync won't erase their work.

<img width="1502" height="1360" alt="image" src="https://github.com/user-attachments/assets/84c953dd-60c4-4dc0-a692-ac354f3797dc" />
