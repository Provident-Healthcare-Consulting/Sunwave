"""build_ur.py — generate Sunwave UR Dashboard at ur/index.html.

Reads data from SQL views (vw_excel_*) via pyodbc.

UR data sources:
  - vw_excel_report_auth      — authorization data
  - vw_excel_census_admitted   — active patient roster
  - vw_excel_group_notes       — group session attendance
"""
import json
import os
import math
import pandas as pd
from datetime import datetime, timezone
from db import get_connection

TEMPLATE = 'dashboard_template_ur.html'
OUTPUT = 'ur/index.html'

conn = get_connection()
print('[UR] Connected to SQL database')


def safe_str(v):
    if v is None:
        return ''
    if isinstance(v, float) and math.isnan(v):
        return ''
    s = str(v).strip()
    return '' if s.lower() in ('nan', 'nat', 'none') else s


def safe_num(v):
    try:
        if v is None or (isinstance(v, float) and math.isnan(v)):
            return 0.0
        return float(v)
    except Exception:
        return 0.0


def fmt_date(v):
    if v is None or pd.isna(v):
        return ''
    if hasattr(v, 'strftime'):
        try:
            return v.strftime('%Y-%m-%d')
        except Exception:
            pass
    return safe_str(v)


# ── Report Auth ─────────────────────────────────────────────────────────────
print('[UR] Loading Report Auth from SQL...')
adf = pd.read_sql('SELECT * FROM dbo.vw_excel_report_auth', conn)
print(f'  {len(adf)} rows from vw_excel_report_auth')

for col in ('admission_date', 'next_review_date'):
    if col in adf.columns:
        adf[col] = pd.to_datetime(adf[col], errors='coerce')
for col in ('authorized_units', 'billed_units_total'):
    if col in adf.columns:
        adf[col] = pd.to_numeric(adf[col], errors='coerce').fillna(0)

auths = []
for _, r in adf.iterrows():
    adm = r.get('admission_date')
    nrd = r.get('next_review_date')
    au = safe_num(r.get('authorized_units'))
    bu = safe_num(r.get('billed_units_total'))
    auths.append({
        'patient':  safe_str(r.get('patient_name')),
        'facility': safe_str(r.get('service_facility')),
        'adm':      fmt_date(adm),
        'nrd':      fmt_date(nrd),
        'code':     safe_str(r.get('authorization_code')),
        'au':       round(au, 1),
        'bu':       round(bu, 1),
        'util':     round((bu / au * 100), 1) if au > 0 else None,
        'ins':      safe_str(r.get('insurance_provider')),
        'reviewer': safe_str(r.get('ur_reviewer')),
    })
print(f'[UR] {len(auths)} authorization rows')

# ── Census_Admitted (active patient roster) ─────────────────────────────────
print('[UR] Loading Census Admitted from SQL...')
cdf = pd.read_sql('SELECT * FROM dbo.vw_excel_census_admitted', conn)
print(f'  {len(cdf)} rows from vw_excel_census_admitted')

census = []
if 'Admission Date' in cdf.columns:
    cdf['Admission Date'] = pd.to_datetime(cdf['Admission Date'], errors='coerce')
for _, r in cdf.iterrows():
    census.append({
        'patient':   safe_str(r.get('Patient Name')),
        'adm':       fmt_date(r.get('Admission Date')),
        'loc':       safe_str(r.get('Admission Level Of Care')),
        'ins':       safe_str(r.get('Insurance Name')),
        'rep':       safe_str(r.get('Admissions Rep')),
        'therapist': safe_str(r.get('Assigned Therapist')),
    })
print(f'[UR] {len(census)} census rows')

# ── GroupNotes (session attendance) ─────────────────────────────────────────
print('[UR] Loading GroupNotes from SQL...')
gdf = pd.read_sql('SELECT * FROM dbo.vw_excel_group_notes', conn)
print(f'  {len(gdf)} rows from vw_excel_group_notes')

gnotes = []
if 'session_date' in gdf.columns:
    gdf['session_date'] = pd.to_datetime(gdf['session_date'], errors='coerce')
if 'length_time' in gdf.columns:
    gdf['length_time'] = pd.to_numeric(gdf['length_time'], errors='coerce').fillna(0)
for _, r in gdf.iterrows():
    gnotes.append({
        'patient': safe_str(r.get('patient_name')),
        'date':    fmt_date(r.get('session_date')),
        'title':   safe_str(r.get('group_title')),
        'status':  safe_str(r.get('status')),
        'mins':    int(safe_num(r.get('length_time'))),
    })
print(f'[UR] {len(gnotes)} group-note rows')

conn.close()

# ── Meta / build info ───────────────────────────────────────────────────────
now = datetime.now(timezone.utc)
meta = {
    'refreshed_at': now.isoformat(),
    'refreshed_human': now.strftime('%A, %B {d}, %Y · {t} UTC').format(
        d=now.day, t=now.strftime('%I:%M %p').lstrip('0')),
    'total_auths':  len(auths),
    'total_census': len(census),
    'total_groupnotes': len(gnotes),
}

# ── Inject into template ────────────────────────────────────────────────────
with open(TEMPLATE, 'r') as f:
    html = f.read()

def inject(html, key, payload):
    placeholder = f'/*INJECT_{key}*/null'
    serialized = json.dumps(payload, separators=(',', ':'), ensure_ascii=True).replace('</', '<\\/')
    if placeholder not in html:
        raise SystemExit(f'Template missing placeholder for {key}')
    return html.replace(placeholder, serialized, 1)

html = inject(html, 'AUTHS',     auths)
html = inject(html, 'CENSUS',    census)
html = inject(html, 'GROUPNOTES', gnotes)
html = inject(html, 'META',      meta)

os.makedirs('ur', exist_ok=True)
with open(OUTPUT, 'w') as f:
    f.write(html)

print(f'[UR] Wrote {OUTPUT}: {os.path.getsize(OUTPUT)/1024:.0f} KB')
print(f'[UR] Auths={len(auths)} Census={len(census)} GroupNotes={len(gnotes)}')
