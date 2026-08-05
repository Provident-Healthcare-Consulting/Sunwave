# CRM Dashboard

**Live URL:** https://icy-moss-07b041e10.7.azurestaticapps.net/crm/

Azure Static Web App serving the CRM & Productivity dashboard. Data is fetched at runtime from the `strive-ur-api` Azure Function App.

## Architecture

```
Browser → /crm/index.html → fetch /api/dashboard/crm → strive-ur-api (Azure Function)
                                                            ↓
                                                      Azure SQL DB
                                                     ┌──────────────────────┐
                                                     │ sunwave_opportunities │
                                                     │ crm_timeline          │
                                                     └──────────────────────┘
```
<img width="1502" height="1360" alt="image" src="https://github.com/user-attachments/assets/84c953dd-60c4-4dc0-a692-ac354f3797dc" />

## Data Sources

**API Endpoint:** `GET /api/dashboard/crm`
**Function App:** `strive-ur-api` (deployed from [UR-Tracking-dev](https://github.com/Provident-Healthcare-Consulting/UR-Tracking-dev) repo)

The API queries **2 SQL tables** and returns **4 arrays**:

| Array   | Source Table             | Description                                              |
|---------|--------------------------|----------------------------------------------------------|
| `OPPS`  | `sunwave_opportunities`  | Direct query — all opportunity records                   |
| `ACTS`  | `crm_timeline`           | Direct query — all timeline/activity records             |
| `USERS` | `crm_timeline` (derived) | Distinct `created_by_name` + `assigned_to` from timeline |
| `TASKS` | `crm_timeline` (derived) | Filtered — rows where `activity_type = 'Task'`          |

### OPPS Column Mapping (sunwave_opportunities → JSON)

| SQL Column         | JSON Key  | Description        |
|--------------------|-----------|--------------------|
| opportunity_id     | id        | Opportunity ID     |
| patient_name       | name      | Patient name       |
| created_on         | co        | Created date       |
| admission_date     | admit     | Admission date     |
| status             | outcome   | Outcome status     |
| stage              | stage     | Pipeline stage     |
| level_of_care      | loc       | Level of care      |
| insurance_name     | ins       | Insurance name     |
| referral_source    | ref       | Referral source    |
| lost_reason        | lost_r    | Lost reason        |
| abandoned_reason   | aband_r   | Abandoned reason   |
| assigned_to        | rep       | Assigned rep       |

### ACTS Column Mapping (crm_timeline → JSON)

| SQL Column           | JSON Key          | Description          |
|----------------------|-------------------|----------------------|
| opportunity_id       | oid               | Linked opportunity   |
| sunwave_timeline_id  | aid               | Timeline event ID    |
| activity_type        | type              | Activity type        |
| task_subject         | subj              | Task subject         |
| description          | text              | Description          |
| created_by_name      | by                | Created by user      |
| workflow_status      | wf                | Workflow status      |
| activity_date        | date              | Activity date        |
| source_type          | assoc             | Association type     |
| assigned_to          | assigned_to_name  | Assigned user        |

## Dashboard Tabs → Data Sources

### 1. Overview (Both tables)
| Visual                   | Source                                          |
|--------------------------|-------------------------------------------------|
| Created / Admitted / Admit Rate / In Pipeline / Lost KPIs | `sunwave_opportunities` — counts by outcome |
| Activities KPI           | `crm_timeline` — count of activity records      |
| Stuck Opportunities      | Both — active OPPS with no human ACTS for >7d   |
| Open CRM Tasks           | `crm_timeline` — TASKS where `is_open = true`   |
| Activity Leaderboard     | `crm_timeline` — ACTS grouped by `created_by_name` |
| Recent Admissions        | Both — admitted OPPS + last human ACT as "closer" |

### 2. Pipeline & Funnel (sunwave_opportunities only)
| Visual                        | Source                                    |
|-------------------------------|-------------------------------------------|
| Created/Active/Scheduled/Admitted/Lost/Abandoned KPIs | OPPS by outcome |
| Stage Distribution funnel + trend | OPPS by `stage`                        |
| Outcome Distribution + trend  | OPPS by `outcome`                         |
| Lost Reason breakdown + trend | OPPS filtered to Lost, grouped by `lost_r` |
| Abandoned Reason breakdown    | OPPS filtered to Abandoned, grouped by `aband_r` |

### 3. User Productivity (crm_timeline only)
| Visual                        | Source                                    |
|-------------------------------|-------------------------------------------|
| Active Users / Total Activities / Median KPIs | ACTS grouped by user  |
| User Productivity Table       | ACTS split by type (Call/Note/Email/SMS/Task/Meeting) per user |
| Per-user activity trend       | ACTS by user × time bucket                |

### 4. User Effectiveness (Both tables)
| Visual                        | Source                                    |
|-------------------------------|-------------------------------------------|
| Opps Touched per user         | ACTS — distinct `oid` per user            |
| Admits Credited per user      | Both — admitted OPPS + all ACTS on those opps |
| Avg Response Time             | Both — OPPS.created_on → first ACT per user per opp |
| Effectiveness table           | Cross-join of OPPS + ACTS                 |

### 5. Opportunity Flow (Both tables)
| Visual                        | Source                                    |
|-------------------------------|-------------------------------------------|
| Searchable opportunity list   | `sunwave_opportunities` — name, ID, stage, outcome, LOC, insurance |
| Expandable timeline per opp   | `crm_timeline` — all ACTS matching opp ID |
| Task Flag / Stage Corrections | Both — derived from ACTS patterns per opp |

### 6. Activity Trends (crm_timeline only)
| Visual                        | Source                                    |
|-------------------------------|-------------------------------------------|
| Activity by Type heatmap      | ACTS bucketed by date × activity_type     |
| Hour × Day-of-Week heatmap   | ACTS by hour and weekday of activity_date |
| Per-user activity trend       | ACTS by user × time bucket                |

### 7. Velocity (Mostly sunwave_opportunities)
| Visual                        | Source                                    |
|-------------------------------|-------------------------------------------|
| Time-to-Schedule (TTS)        | OPPS — `created_on` → scheduled date      |
| Time-to-Admit (TSA)           | OPPS — scheduled date → `admission_date`  |
| Total Time-to-Admit (TTA)     | OPPS — `created_on` → `admission_date`    |
| First-Touch Response Time     | Both — OPPS.created_on → first human ACT  |
| Per-rep TTS matrix            | Both — OPPS dates + `assigned_to` from ACTS |

### 8. Composition (sunwave_opportunities only)
| Visual                        | Source                                    |
|-------------------------------|-------------------------------------------|
| Top 5 Referral Sources trend  | OPPS — `referral_source` by creation date |
| Insurance Mix on Admits       | OPPS — `insurance_name` on admitted opps  |
| LOC Mix on Admits             | OPPS — `level_of_care` on admitted opps   |
| Referral Type Mix on Admits   | OPPS — `referral_source` on admitted only |

## Authentication

MSAL browser auth — restricted to `@gshealthcarellc.com` and `@providenthcc.com` tenant accounts.

## Deployment

Pushes to `main` trigger the Azure Static Web Apps CI/CD workflow which deploys to `icy-moss-07b041e10.7.azurestaticapps.net`.

## CORS

The `strive-ur-api` Function App must have `https://icy-moss-07b041e10.7.azurestaticapps.net` in its CORS allowed origins.
